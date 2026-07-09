import heapq
from .models import Waypoint, Edge


def build_graph(accessible_only=False):
    """
    Build an adjacency list graph from the Edge model.
    Returns: dict { waypoint_id: [(distance, neighbour_id), ...] }
    """
    graph = {}

    # Initialize all active waypoints
    waypoints = Waypoint.objects.filter(is_active=True)
    for wp in waypoints:
        graph[wp.id] = []

    # Load edges
    edges = Edge.objects.filter(is_active=True).select_related(
        'from_waypoint', 'to_waypoint'
    )
    if accessible_only:
        edges = edges.filter(is_accessible=True)

    for edge in edges:
        fid = edge.from_waypoint.id
        tid = edge.to_waypoint.id
        dist = edge.distance

        if fid in graph:
            graph[fid].append((dist, tid))
        # Treat all edges as bidirectional
        if tid in graph:
            graph[tid].append((dist, fid))

    return graph


def dijkstra(graph, start_id, end_id):
    """
    Standard Dijkstra's algorithm using a min-heap.
    Returns: (total_distance, [waypoint_id path]) or (None, []) if no path
    """
    # Priority queue: (distance, waypoint_id)
    heap = [(0, start_id)]
    distances = {start_id: 0}
    previous = {start_id: None}
    visited = set()

    while heap:
        current_dist, current_id = heapq.heappop(heap)

        if current_id in visited:
            continue
        visited.add(current_id)

        if current_id == end_id:
            break

        for edge_dist, neighbour_id in graph.get(current_id, []):
            new_dist = current_dist + edge_dist

            if neighbour_id not in distances or new_dist < distances[neighbour_id]:
                distances[neighbour_id] = new_dist
                previous[neighbour_id] = current_id
                heapq.heappush(heap, (new_dist, neighbour_id))

    # Reconstruct path
    if end_id not in distances:
        return None, []

    path = []
    current = end_id
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()

    return distances[end_id], path


def get_route(origin_building, destination_building, accessible_only=False):
    """
    Find the shortest route between two buildings.
    Looks for the nearest waypoint attached to each building.
    Returns: (total_distance, [Waypoint objects]) or (None, [])
    """
    # Get entry waypoints for each building
    origin_waypoints = Waypoint.objects.filter(
        building=origin_building, is_active=True
    )
    destination_waypoints = Waypoint.objects.filter(
        building=destination_building, is_active=True
    )

    if not origin_waypoints.exists() or not destination_waypoints.exists():
        return None, []

    graph = build_graph(accessible_only=accessible_only)

    best_distance = None
    best_path = []

    # Try all origin/destination waypoint combinations, pick shortest
    for origin_wp in origin_waypoints:
        for dest_wp in destination_waypoints:
            dist, path_ids = dijkstra(graph, origin_wp.id, dest_wp.id)
            if dist is not None:
                if best_distance is None or dist < best_distance:
                    best_distance = dist
                    best_path = path_ids

    if not best_path:
        return None, []

    # Fetch full waypoint objects in path order
    waypoint_map = {
        wp.id: wp for wp in Waypoint.objects.filter(id__in=best_path)
    }
    ordered_waypoints = [waypoint_map[wid] for wid in best_path if wid in waypoint_map]

    return best_distance, ordered_waypoints