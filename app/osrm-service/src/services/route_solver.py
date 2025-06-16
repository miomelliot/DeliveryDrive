from datetime import time
from uuid import UUID

from loguru import logger
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from src.schemas.logistics import Create, Order, Solver


def _to_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def _add_capacity_dimension(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    orders: list[Order],
    creates: list[Create],
) -> None:
    demands: list[int] = [0] + [int(o.weight) for o in orders]
    capacities: list[int] = [int(c.transport_type.capacity) for c in creates]

    def demand_callback(index: int) -> int:
        node = int(manager.IndexToNode(index))
        return demands[node]

    demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_index,
        0,
        capacities,
        True,
        "Capacity",
    )


def _add_time_dimension(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    distance_matrix: list[list[float]],
    orders: list[Order],
    creates: list[Create],
    solver_cfg: Solver,
) -> None:
    service_times: list[int] = [0] + [int(o.service_duration) for o in orders]

    def time_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel = distance_matrix[from_node][to_node]
        return int(travel + service_times[from_node])

    time_index = routing.RegisterTransitCallback(time_callback)
    horizon: int = 24 * 60 * 60
    routing.AddDimension(
        time_index,
        horizon if solver_cfg.allow_waiting else 0,
        horizon,
        False,
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    for i, order in enumerate(orders, start=1):
        idx = manager.NodeToIndex(i)
        start = _to_seconds(order.time_window[0])
        end = _to_seconds(order.time_window[1])
        time_dimension.CumulVar(idx).SetRange(start, end)

    for vid, cr in enumerate(creates):
        start = _to_seconds(cr.time_window[0])
        end = _to_seconds(cr.time_window[1])
        time_dimension.CumulVar(routing.Start(vid)).SetRange(start, end)
        time_dimension.CumulVar(routing.End(vid)).SetRange(start, end)


def _extract_routes(
    routing: pywrapcp.RoutingModel,
    manager: pywrapcp.RoutingIndexManager,
    solution: pywrapcp.Assignment,
    orders: list[Order],
    creates: list[Create],
) -> list[list[UUID]]:
    routes: list[list[UUID]] = []
    for vehicle_id in range(len(creates)):
        index = routing.Start(vehicle_id)
        vehicle_route: list[UUID] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                vehicle_route.append(orders[node - 1].order_id)
            index = solution.Value(routing.NextVar(index))
        routes.append(vehicle_route)
    return routes


def solve_vrp(
    distance_matrix: list[list[float]],
    orders: list[Order],
    creates: list[Create],
    solver_cfg: Solver,
) -> list[list[UUID]]:
    logger.debug("Solving VRP: %d orders, %d vehicles", len(orders), len(creates))
    num_nodes: int = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(num_nodes, len(creates), 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    distance_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_index)

    _add_capacity_dimension(routing, manager, orders, creates)
    _add_time_dimension(routing, manager, distance_matrix, orders, creates, solver_cfg)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.time_limit.FromSeconds(solver_cfg.max_runtime_sec)
    search_params.solution_limit = solver_cfg.num_solutions
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_params)
    if solution is None:
        logger.warning("VRP solver returned no solution")
        return []

    routes = _extract_routes(routing, manager, solution, orders, creates)
    logger.debug("VRP solver produced %d routes", len(routes))
    return routes
