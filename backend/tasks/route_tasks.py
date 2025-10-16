"""
Route generation tasks for RQ workers.
"""
import redis
from rq import Queue

from ..services.route_planner import RoutePlanner
from ..services.geoapify_client import GeoAPIfyClient
from ..services.osm_client import OSMClient
from ..services.cache_service import CacheService
from ..regions.registry import region_registry
from ..config import REDIS_URL

# Configure Redis connection
conn = redis.from_url(REDIS_URL)
route_queue = Queue('route_generation', connection=conn)


def generate_route_task(region_id, num_days=None, max_tries=None, good_enough_threshold=None):
    """
    Generate a hiking route for any region.
    
    Args:
        region_id: ID of the region
        num_days: Number of days for the route
        max_tries: Maximum number of attempts
        good_enough_threshold: Threshold for early termination
    
    Returns:
        Route generation result
    """
    print(f"[LOG] Starting route generation for region: {region_id}")
    
    try:
        # Initialize route planner (it initializes its own dependencies)
        route_planner = RoutePlanner()
        
        # Generate route
        result = route_planner.generate_route(
            region_id=region_id,
            num_days=num_days,
            max_tries=max_tries,
            good_enough_threshold=good_enough_threshold
        )
        
        if not result:
            return {
                'status': 'error',
                'message': f'No valid route found for region {region_id}'
            }
        
        # Export to GeoJSON
        geojson_data = route_planner.export_route_to_geojson(region_id, result)
        
        # Calculate summary
        total_distance = sum(leg['properties']['distance'] for leg in result['legs']) / 1000
        total_duration = sum(leg['properties']['time'] for leg in result['legs']) / 60
        scenic_points = [mid['name'] for mid in result['scenic_midpoints'] if mid]
        
        return {
            'status': 'success',
            'geojson': geojson_data,
            'route_summary': {
                'waypoints': result['waypoints'],
                'total_distance_km': total_distance,
                'total_duration_min': total_duration,
                'scenic_points': scenic_points
            },
            'message': f'Route generated successfully for {region_id}'
        }
        
    except Exception as e:
        print(f"[LOG] Exception in generate_route_task for {region_id}: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
