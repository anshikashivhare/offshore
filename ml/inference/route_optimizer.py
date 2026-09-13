"""
Vessel route optimizer for Antarctic navigation.

Builds a grid graph where each cell's traversal cost is derived from
sea-ice concentration (0.0 = open water, 1.0 = fully ice-covered),
then runs A* to find the safest / most fuel-efficient path between
two points.
"""

import networkx as nx
import numpy as np


def build_grid_graph(
    concentration_grid: np.ndarray, max_passable_concentration: float = 0.9
):
    rows, cols = concentration_grid.shape
    G = nx.Graph()

    def cost(r, c):
        conc = concentration_grid[r, c]
        return 1.0 + (conc**2) * 20.0

    for r in range(rows):
        for c in range(cols):
            if concentration_grid[r, c] >= max_passable_concentration:
                continue
            G.add_node((r, c))

    neighbor_offsets = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ]

    for r, c in list(G.nodes):
        for dr, dc in neighbor_offsets:
            nr, nc = r + dr, c + dc
            if (nr, nc) in G.nodes:
                diag_factor = 1.41 if dr != 0 and dc != 0 else 1.0
                edge_cost = ((cost(r, c) + cost(nr, nc)) / 2) * diag_factor
                G.add_edge((r, c), (nr, nc), weight=edge_cost)

    return G


def heuristic(a, b):
    return np.hypot(a[0] - b[0], a[1] - b[1])


def find_route(
    concentration_grid: np.ndarray,
    start: tuple,
    end: tuple,
    max_passable_concentration: float = 0.9,
):
    G = build_grid_graph(concentration_grid, max_passable_concentration)

    if start not in G.nodes or end not in G.nodes:
        return {
            "status": "no_path_found",
            "path": [],
            "total_cost": None,
            "reason": "start or end point is impassable or out of bounds",
        }

    try:
        path = nx.astar_path(G, start, end, heuristic=heuristic, weight="weight")
        total_cost = nx.path_weight(G, path, weight="weight")
        return {"status": "ok", "path": path, "total_cost": round(total_cost, 2)}
    except nx.NetworkXNoPath:
        return {
            "status": "no_path_found",
            "path": [],
            "total_cost": None,
            "reason": "no passable route exists between start and end",
        }


def grid_to_latlon(path, origin_lat, origin_lon, cell_size_deg=0.1):
    return [
        {
            "lat": round(origin_lat - row * cell_size_deg, 5),
            "lon": round(origin_lon + col * cell_size_deg, 5),
        }
        for row, col in path
    ]


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    grid = rng.uniform(0, 0.6, size=(20, 20))
    grid[8:12, 5:15] = 0.95

    result = find_route(grid, start=(0, 0), end=(19, 19))
    print("Status:", result["status"])
    print("Total cost:", result["total_cost"])
    print("Path length (cells):", len(result["path"]))
