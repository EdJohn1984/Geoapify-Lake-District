"""
Geometry utilities for route planning.
"""
from typing import List, Tuple
from geopy.distance import geodesic


def calculate_route_overlap(leg1_coords: List[Tuple[float, float]], leg2_coords: List[Tuple[float, float]]) -> float:
    """
    Calculate overlap between two route legs.
    
    Args:
        leg1_coords: Coordinates from first leg
        leg2_coords: Coordinates from second leg
    
    Returns:
        Overlap ratio (0-1)
    """
    if not leg1_coords or not leg2_coords:
        return 0
    
    # Convert to sets of coordinate tuples for comparison
    set1 = set(leg1_coords)
    set2 = set(leg2_coords)
    
    # Calculate overlap as intersection over union
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0
    
    overlap = intersection / union
    return overlap


def find_best_scenic_midpoint(
    start_coords: Tuple[float, float], 
    end_coords: Tuple[float, float], 
    scenic_points: List[dict], 
    search_radius_km: float = 10
) -> dict:
    """
    Find the best scenic midpoint between two coordinates.
    
    Args:
        start_coords: (lat, lon) of start point
        end_coords: (lat, lon) of end point
        scenic_points: List of scenic point data
        search_radius_km: Search radius in kilometers
    
    Returns:
        Best scenic point or None
    """
    # Calculate midpoint between start and end
    mid_lat = (start_coords[0] + end_coords[0]) / 2
    mid_lon = (start_coords[1] + end_coords[1]) / 2
    
    if not scenic_points:
        # Fallback: no scenic dataset available, synthesize a geometric midpoint
        return {
            'name': 'Midpoint',
            'type': 'Midpoint',
            'coords': (mid_lat, mid_lon)
        }
    
    # Find scenic points within search radius of the midpoint
    best_point = None
    min_distance = float('inf')
    
    for point in scenic_points:
        # scenic_points coords are [lon, lat]; geodesic expects (lat, lon)
        point_lat, point_lon = point['coords'][1], point['coords'][0]
        dist = geodesic((mid_lat, mid_lon), (point_lat, point_lon)).kilometers
        if dist < search_radius_km and dist < min_distance:
            best_point = point
            min_distance = dist
    
    if best_point:
        return best_point

    # Fallback: choose the closest scenic point to the geometric midpoint, even if outside radius
    print(f"[LOG] No scenic midpoint within {search_radius_km}km; falling back to nearest scenic point to midpoint ({mid_lat}, {mid_lon})")
    nearest_point = None
    nearest_distance = float('inf')
    for point in scenic_points:
        point_lat, point_lon = point['coords'][1], point['coords'][0]
        dist = geodesic((mid_lat, mid_lon), (point_lat, point_lon)).kilometers
        if dist < nearest_distance:
            nearest_distance = dist
            nearest_point = point

    return nearest_point


def calculate_feasible_pairs(waypoints: List[dict], min_distance_km: float, max_distance_km: float) -> List[dict]:
    """
    Calculate feasible pairs between waypoints based on distance constraints.
    
    Args:
        waypoints: List of waypoint data
        min_distance_km: Minimum distance between waypoints
        max_distance_km: Maximum distance between waypoints
    
    Returns:
        List of feasible pairs
    """
    # Build stable, unique identifiers for waypoints to avoid name collisions
    def _waypoint_key(wp: dict) -> Tuple[str, float, float]:
        props = wp.get('properties', {})
        geom = wp.get('geometry', {})
        coords = geom.get('coordinates', [None, None])
        if coords is None or len(coords) < 2:
            return ("", None, None)
        lon, lat = coords[0], coords[1]
        # Prefer explicit IDs when present; otherwise synthesize from name and rounded coords
        wp_id = props.get('id') or props.get('osm_id') or props.get('ref')
        if not wp_id:
            name = props.get('name', 'Unnamed')
            wp_id = f"{name}:{round(lat, 5)},{round(lon, 5)}"
        return (str(wp_id), lat, lon)

    keyed_points: List[Tuple[str, float, float]] = []
    for wp in waypoints:
        wp_id, lat, lon = _waypoint_key(wp)
        if wp_id and lat is not None and lon is not None:
            keyed_points.append((wp_id, lat, lon))

    # Deduplicate exact duplicates while preserving distinct points that share a name
    seen = {}
    for wp_id, lat, lon in keyed_points:
        seen[(wp_id, lat, lon)] = (lat, lon)

    items = list(seen.items())  # [((id, lat, lon), (lat, lon)), ...]

    # Calculate distances between all ordered pairs (A->B and B->A) within constraints
    feasible_pairs: List[dict] = []
    for i in range(len(items)):
        (id1, lat1, lon1), (lat1v, lon1v) = items[i]
        for j in range(len(items)):
            if i == j:
                continue
            (id2, lat2, lon2), (lat2v, lon2v) = items[j]
            dist = geodesic((lat1v, lon1v), (lat2v, lon2v)).kilometers
            if min_distance_km <= dist <= max_distance_km:
                feasible_pairs.append({
                    'from': id1,
                    'to': id2,
                    'distance': dist
                })

    return feasible_pairs
