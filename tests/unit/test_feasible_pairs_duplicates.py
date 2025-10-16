"""
Unit tests for feasible pair calculation with duplicate waypoint names.
"""
from backend.utils.geometry import calculate_feasible_pairs


def _feature(name: str, lon: float, lat: float):
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def test_duplicate_names_do_not_collapse_waypoints():
    # Two distinct points share the same name but are ~10.4km apart (within 10-15km band)
    a = _feature("Summit", -3.00, 54.00)
    b = _feature("Summit", -3.16, 54.00)
    # Third point outside range to ensure it is excluded
    c = _feature("Ridge", -3.50, 54.00)

    waypoints = [a, b, c]

    pairs = calculate_feasible_pairs(waypoints, min_distance_km=10.0, max_distance_km=15.0)

    # Expect exactly two ordered pairs between the two Summits: a->b and b->a
    assert len(pairs) == 2

    from_ids = {p["from"] for p in pairs}
    to_ids = {p["to"] for p in pairs}

    # IDs should be synthesized to include coordinates, preventing name collision
    assert any(fid.startswith("Summit:") for fid in from_ids)
    assert any(tid.startswith("Summit:") for tid in to_ids)


