from datetime import time
from typing import Any
from uuid import UUID

from loguru import logger
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from src.schemas.logistics import Create, Order, Solver


def _to_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


# ───────────────────────── Capacity ─────────────────────────
def _add_capacity_dimension(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    orders: list[Order],
    creates: list[Create],
) -> None:
    logger.debug("Setting up capacity dimension")
    demands: list[int] = [0] + [int(o.weight) for o in orders]
    capacities: list[int] = [int(c.transport_type.capacity) for c in creates]
    logger.debug(f"Demands: {demands}")
    logger.debug(f"Vehicle capacities: {capacities}")

    def demand_callback(index: int) -> int:
        node = int(manager.IndexToNode(index))
        return demands[node]

    demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
    logger.debug(f"Demand callback registered with index {demand_index}")
    routing.AddDimensionWithVehicleCapacity(
        demand_index,
        0,
        capacities,
        True,
        "Capacity",
    )
    logger.debug("Capacity dimension added")


# ───────────────────────── Time (soft windows) ─────────────────────────
def _add_time_dimension(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    distance_matrix: list[list[float]],
    orders: list[Order],
    creates: list[Create],
    solver_cfg: Solver,
) -> None:
    logger.debug("Setting up time dimension")
    service_times: list[int] = [0] + [int(o.service_duration) for o in orders]
    logger.debug(f"Service times: {service_times}")

    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel = distance_matrix[from_node][to_node]
        return int(travel + service_times[from_node])

    time_index = routing.RegisterTransitCallback(time_callback)
    logger.debug(f"Time callback registered with index {time_index}")

    horizon = 24 * 60 * 60
    wait_status = "enabled" if solver_cfg.allow_waiting else "disabled"
    logger.debug(f"Using horizon {horizon} with waiting {wait_status}")

    routing.AddDimension(
        time_index,
        horizon if solver_cfg.allow_waiting else 0,
        horizon,
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    penalty: Any | int = getattr(solver_cfg, "time_window_penalty", 10)

    # ---- orders --------------------------------------------------------
    for i, order in enumerate(orders, start=1):
        idx = manager.NodeToIndex(i)
        start = _to_seconds(order.time_window[0])
        end = _to_seconds(order.time_window[1])

        # базовый диапазон
        time_dimension.CumulVar(idx).SetRange(start, end)

        time_dimension.SetCumulVarSoftUpperBound(idx, end, penalty)

        logger.debug(f"Order {order.order_id} time window {start}-{end} with soft penalty {penalty}/sec")

    # ---- vehicles (start/end) -----------------------------------------
    for vid, cr in enumerate(creates):
        start = _to_seconds(cr.time_window[0])
        end = _to_seconds(cr.time_window[1])

        for node in (routing.Start(vid), routing.End(vid)):
            time_dimension.CumulVar(node).SetRange(start, end)
            time_dimension.SetCumulVarSoftUpperBound(node, end, penalty)

        logger.debug(f"Vehicle {vid} soft window {start}-{end}")

    logger.debug("Time dimension added")


# ───────────────────────── Extract routes ─────────────────────────
def _extract_routes(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    solution: pywrapcp.Assignment,
    orders: list[Order],
    creates: list[Create],
) -> list[list[UUID]]:
    logger.debug("Extracting routes from solution")
    routes: list[list[UUID]] = []
    for vehicle_id in range(len(creates)):
        index = routing.Start(vehicle_id)
        logger.debug(f"Vehicle {vehicle_id} start index {index}")
        vehicle_route: list[UUID] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            logger.debug(f"Vehicle {vehicle_id} visiting node {node}")
            if node != 0:
                vehicle_route.append(orders[node - 1].order_id)
            index = solution.Value(routing.NextVar(index))
        routes.append(vehicle_route)
        logger.debug(f"Vehicle {vehicle_id} route: {vehicle_route}")
    logger.debug("Extraction complete")
    return routes


# ───────────────────────── Solver orchestrator ─────────────────────────
def solve_vrp(
    distance_matrix: list[list[float]],
    orders: list[Order],
    creates: list[Create],
    solver_cfg: Solver,
) -> list[list[UUID]]:
    logger.debug(f"Solving VRP: {len(orders)} orders, {len(creates)} vehicles")

    num_nodes: int = len(distance_matrix)
    logger.debug(f"Creating routing manager for {num_nodes} nodes")

    manager = pywrapcp.RoutingIndexManager(num_nodes, len(creates), 0)
    routing = pywrapcp.RoutingModel(manager)
    logger.debug("Routing model initialized")

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    distance_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_index)
    logger.debug(f"Distance callback registered with index {distance_index}")
    logger.debug("Arc cost evaluator set for all vehicles")

    # Подключение ограничений
    _add_capacity_dimension(routing, manager, orders, creates)
    _add_time_dimension(routing, manager, distance_matrix, orders, creates, solver_cfg)

    # Параметры поиска
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.time_limit.FromSeconds(solver_cfg.max_runtime_sec)
    search_params.solution_limit = solver_cfg.num_solutions
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH

    # Многопоточность
    try:
        search_params.num_search_workers = solver_cfg.num_search_workers
    except AttributeError:
        logger.warning("ORTools: num_search_workers not supported — fallback to single thread")

    logger.debug(
        f"Search parameters: time_limit={solver_cfg.max_runtime_sec}, "
        f"solutions={solver_cfg.num_solutions}, workers={solver_cfg.num_search_workers}, "
        f"strategy=PATH_CHEAPEST_ARC, metaheuristic=GUIDED_LOCAL_SEARCH"
    )

    logger.debug("Starting solver")
    solution = routing.SolveWithParameters(search_params)
    if solution is None:
        logger.warning("VRP solver returned no solution")
        return []

    logger.debug(f"Solver finished with objective value {solution.ObjectiveValue()}")
    routes: list[list[UUID]] = _extract_routes(routing, manager, solution, orders, creates)
    logger.debug(f"VRP solver produced {len(routes)} routes")

    return routes
