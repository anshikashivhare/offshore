from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node


def test_final_approach_refines_a_coarse_coastal_diagonal():
    planner = AStarRoutePlanner(resolution=0.5)
    coarse_path = [Node(25.5, -15.0), Node(27.0, -13.5)]

    refined = planner._refine_final_approach(coarse_path, coarse_path[-1])

    assert len(refined) > len(coarse_path)
    assert refined[-1] == coarse_path[-1]
    # The problematic single diagonal is replaced by a coastal sequence.
    assert refined[-2] != coarse_path[0]
