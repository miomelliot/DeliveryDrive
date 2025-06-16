from uuid import UUID

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from src.schemas.logistics import Create, Order, Solver


def solve_vrp(
    distance_matrix: list[list[float]],
    orders: list[Order],
    creates: list[Create],
    solver_cfg: Solver,
) -> list[list[UUID]]:
    num_nodes: int = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(num_nodes, len(creates), 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

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

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.time_limit.FromSeconds(solver_cfg.max_runtime_sec)
    search_params.solution_limit = solver_cfg.num_solutions
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_params)
    if solution is None:
        return []

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
