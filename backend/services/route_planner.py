"""
Unified route planner service for all regions.
"""
import random
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from ..models.region import Region
from ..regions.registry import region_registry
from ..services.geoapify_client import GeoAPIfyClient, RouteResult
from ..services.osm_client import OSMClient
from ..services.cache_service import CacheService
from ..utils.geometry import calculate_route_overlap, find_best_scenic_midpoint, calculate_feasible_pairs
from ..utils.terrain_analysis import analyze_surface_types
from ..config import SCENIC_SEARCH_RADIUS_KM, DEFAULT_MAX_TRIES, DEFAULT_GOOD_ENOUGH_THRESHOLD


class RoutePlanner:
    """Unified route planner for all regions."""
    
    def __init__(self):
        self.geoapify_client = GeoAPIfyClient()
        self.osm_client = OSMClient()
        self.cache_service = CacheService()
    
    def generate_route(
        self, 
        region_id: str, 
        num_days: int = None, 
        max_tries: int = None, 
        good_enough_threshold: float = None
    ) -> Optional[Dict]:
        """
        Generate a hiking route for a region.
        
        Args:
            region_id: ID of the region
            num_days: Number of days for the route
            max_tries: Maximum number of attempts
            good_enough_threshold: Threshold for early termination
        
        Returns:
            Route data or None if failed
        """
        # Get region configuration
        region = region_registry.get_region(region_id)
        if not region:
            raise ValueError(f"Region not found: {region_id}")
        
        # Use defaults if not specified
        num_days = num_days or region.route_params.default_days
        max_tries = max_tries or DEFAULT_MAX_TRIES
        good_enough_threshold = good_enough_threshold or DEFAULT_GOOD_ENOUGH_THRESHOLD
        
        print(f"[LOG] Starting {region.name} route generation")
        
        # Load waypoints
        waypoints = region_registry.load_waypoints(region_id)
        
        # Build lookup keyed the same way as feasible pair IDs (name with coords fallback)
        def _waypoint_key(wp: Dict) -> str:
            props = wp.get('properties', {})
            geom = wp.get('geometry', {})
            coords = geom.get('coordinates', [None, None])
            lon, lat = coords[0], coords[1]
            wp_id = props.get('id') or props.get('osm_id') or props.get('ref')
            if not wp_id:
                name = props.get('name', 'Unnamed')
                wp_id = f"{name}:{round(lat, 5)},{round(lon, 5)}"
            return str(wp_id)
        
        waypoint_by_key: Dict[str, Dict] = {}
        id_to_name: Dict[str, str] = {}
        for wp in waypoints:
            key = _waypoint_key(wp)
            waypoint_by_key[key] = wp
            id_to_name[key] = wp.get('properties', {}).get('name', key)
        
        # Get feasible pairs
        feasible_pairs = self._get_feasible_pairs(region_id, waypoints)
        if not feasible_pairs:
            print("[LOG] No feasible pairs found")
            return None
        
        print(f"[LOG] Found {len(feasible_pairs)} feasible pairs")
        
        # Get scenic points
        scenic_points = self._get_scenic_points(region_id)
        print(f"[LOG] Found {len(scenic_points)} scenic points")
        
        # Create lookup dictionary for faster access
        feasible_next_steps = {}
        for pair in feasible_pairs:
            start = pair['from']
            end = pair['to']
            if start not in feasible_next_steps:
                feasible_next_steps[start] = []
            feasible_next_steps[start].append(end)
        
        best_score = float('inf')
        best_route = None
        
        # Try to generate a valid route
        for attempt in range(max_tries):
            print(f"[LOG] Try {attempt + 1}/{max_tries}")
            
            # Start with a random waypoint ID that has feasible next steps and exists in waypoints
            valid_starts = [wp_id for wp_id in feasible_next_steps.keys() if wp_id in waypoint_by_key]
            if not valid_starts:
                print("[LOG] No valid starting points found")
                break
            
            current_id = random.choice(valid_starts)
            route_names = [id_to_name.get(current_id, current_id)]
            used_ids = {current_id}
            route_legs = []
            scenic_midpoints = []
            
            # Build route day by day
            for day in range(num_days):
                print(f"[LOG]  Day {day + 1}: Generating leg from {current_id}")
                
                # Get possible next steps from feasible pairs
                if current_id not in feasible_next_steps:
                    print(f"[LOG]  No feasible next steps from {current_id}")
                    break
                
                next_steps = [next_point for next_point in feasible_next_steps[current_id] 
                             if next_point not in used_ids and next_point in waypoint_by_key]
                
                if not next_steps:
                    print(f"[LOG]  No unused feasible next steps from {current_id}")
                    break
                
                # Choose a random next step from feasible options
                next_id = random.choice(next_steps)
                
                # Get coordinates for current and next point
                current_coords = waypoint_by_key[current_id]['geometry']['coordinates']
                next_coords = waypoint_by_key[next_id]['geometry']['coordinates']
                
                # Find scenic midpoint
                midpoint = find_best_scenic_midpoint(
                    (current_coords[1], current_coords[0]),  # (lat, lon)
                    (next_coords[1], next_coords[0]),        # (lat, lon)
                    scenic_points,
                    SCENIC_SEARCH_RADIUS_KM
                )
                
                # Get route between current and next point, via midpoint if available
                route_data = self._get_route_with_midpoint(
                    current_coords, next_coords, midpoint, region.route_params.mode
                )
                if not route_data:
                    print(f"[LOG]  No route found from {current_id} to {next_id}")
                    break
                
                # Add to route
                route_names.append(id_to_name.get(next_id, next_id))
                used_ids.add(next_id)
                route_legs.append(route_data)
                # Always align scenic_midpoints length with legs
                scenic_midpoints.append(midpoint if midpoint else None)
                current_id = next_id
            
            # If we have a complete route, calculate its score
            if len(route_names) == num_days + 1:
                # Calculate overlap between legs
                overlap = 0
                for i in range(len(route_legs) - 1):
                    overlap += calculate_route_overlap(route_legs[i]['coords'], route_legs[i+1]['coords'])
                
                # Calculate score (lower is better)
                score = overlap / (num_days - 1)  # Average overlap per leg
                print(f"[LOG] Route score: {score:.3f}")
                
                if score < best_score:
                    best_score = score
                    best_route = {
                        'waypoints': route_names,
                        'legs': route_legs,
                        'scenic_midpoints': scenic_midpoints
                    }
                    print(f"[LOG] New best {region.name} itinerary found with score {score:.3f}")
                    
                    # If we found a route that's good enough, return it immediately
                    if score <= good_enough_threshold:
                        print(f"[LOG] Found route with score {score:.3f} below threshold {good_enough_threshold}")
                        return best_route
        
        if best_route:
            print(f"[LOG] Found valid {region.name} route with score {best_score:.3f}")
            return best_route
        else:
            print(f"[LOG] No valid {region.name} route found")
            return None
    
    def export_route_to_geojson(self, region_id: str, route_data: Dict) -> Dict:
        """
        Export route data as GeoJSON for interactive web maps.
        
        Args:
            region_id: ID of the region
            route_data: Route data from generate_route
        
        Returns:
            GeoJSON data
        """
        region = region_registry.get_region(region_id)
        if not region:
            raise ValueError(f"Region not found: {region_id}")
        
        waypoints = region_registry.load_waypoints(region_id)
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Add route waypoints
        for i, waypoint_name in enumerate(route_data['waypoints']):
            if waypoint_name in waypoint_dict:
                wp = waypoint_dict[waypoint_name]
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": waypoint_name,
                        "day": i + 1 if i < len(route_data['waypoints']) - 1 else "End",
                        "type": "waypoint",
                        "marker_color": ["blue", "green", "purple", "orange"][i % 4],
                        "description": f"Day {i + 1} {'Start' if i == 0 else 'End' if i == len(route_data['waypoints']) - 1 else 'End/Start'}"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": wp['geometry']['coordinates']
                    }
                }
                geojson["features"].append(feature)
        
        # Add route legs as LineString features with surface data
        for i, leg in enumerate(route_data['legs']):
            # Get surface data for this route leg
            print(f"[LOG] Getting surface data for {region.name} day {i + 1}...")
            surface_data = self.osm_client.get_surface_data(leg['coords'])
            surface_analysis = analyze_surface_types(surface_data, region.terrain_defaults.__dict__)
            
            feature = {
                "type": "Feature",
                "properties": {
                    "name": f"Day {i+1}",
                    "day": i + 1,
                    "distance_km": round(leg['properties']['distance'] / 1000, 1),
                    "duration_min": round(leg['properties']['time'] / 60, 0),
                    "type": "route_leg",
                    "color": ["red", "green", "purple", "orange", "brown"][i % 5],
                    "description": f"Day {i + 1}: {leg['properties']['distance']/1000:.1f}km, {leg['properties']['time']/60:.0f}min",
                    "surface_data": surface_analysis
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": leg['coords']
                }
            }
            geojson["features"].append(feature)
        
        # Add scenic midpoints
        for i, midpoint in enumerate(route_data['scenic_midpoints']):
            if midpoint:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": midpoint['name'],
                        "type": midpoint['type'],
                        "day": i + 1,
                        "marker_type": "scenic",
                        "description": f"Scenic {midpoint['type']}: {midpoint['name']}"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [midpoint['coords'][0], midpoint['coords'][1]]
                    }
                }
                geojson["features"].append(feature)
        
        return geojson
    
    def _get_feasible_pairs(self, region_id: str, waypoints: List[Dict]) -> List[Dict]:
        """Get or compute feasible pairs for a region."""
        # Try cache first
        cached_pairs = self.cache_service.get_feasible_pairs(region_id)
        if cached_pairs:
            return cached_pairs
        
        # Compute feasible pairs
        region = region_registry.get_region(region_id)
        feasible_pairs = calculate_feasible_pairs(
            waypoints,
            region.route_params.min_distance_km,
            region.route_params.max_distance_km
        )
        
        # Cache the results
        self.cache_service.set_feasible_pairs(region_id, feasible_pairs)
        return feasible_pairs
    
    def _get_scenic_points(self, region_id: str) -> List[Dict]:
        """Get or fetch scenic points for a region."""
        # Try cache first
        cached_points = self.cache_service.get_scenic_points(region_id)
        if cached_points:
            return cached_points
        
        # Fetch from API
        region = region_registry.get_region(region_id)
        bbox_string = region.bbox.to_bbox_string()
        
        scenic_points = self.geoapify_client.get_scenic_points(
            bbox_string,
            region.scenic_categories,
            limit=100
        )
        
        # Cache the results
        self.cache_service.set_scenic_points(region_id, scenic_points)
        return scenic_points
    
    def _get_route_with_midpoint(
        self, 
        start_coords: List[float], 
        end_coords: List[float], 
        midpoint: Optional[Dict], 
        mode: str
    ) -> Optional[Dict]:
        """Get route between coordinates, optionally via a midpoint."""
        # Prepare waypoints
        waypoints = [(start_coords[1], start_coords[0])]  # (lat, lon)
        
        if midpoint:
            waypoints.append((midpoint['coords'][1], midpoint['coords'][0]))  # (lat, lon)
        
        waypoints.append((end_coords[1], end_coords[0]))  # (lat, lon)
        
        # Get route from GeoAPIfy
        route_result = self.geoapify_client.get_route(waypoints, mode)
        if not route_result:
            return None
        
        # Convert to expected format
        return {
            'properties': route_result.properties,
            'geometry': route_result.geometry,
            'coords': route_result.coords
        }
