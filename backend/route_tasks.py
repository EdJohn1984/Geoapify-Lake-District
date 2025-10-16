"""
Route generation tasks for RQ workers.
These functions are separate from the main app module to avoid serialization issues.
"""

import json
from geoapify_planner import generate_hiking_route, export_route_to_geojson
from cornwall_planner import generate_cornwall_hiking_route, export_cornwall_route_to_geojson

def generate_route():
    """Generate a Lake District hiking route."""
    print("[LOG] Starting generate_route")
    try:
        # Load waypoints from file
        with open('filtered_waypoints.json', 'r') as f:
            waypoints = json.load(f)
            
        # Create a dictionary of waypoint names
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        # Always generate a 3-day hiking route dynamically
        result = generate_hiking_route(waypoint_dict, num_days=3)
        print("[LOG] generate_hiking_route finished")
        if not result:
            print("[LOG] No valid route found")
            return {
                'status': 'error',
                'message': 'No valid route found'
            }
            
        # Format the response
        print("[LOG] Route generated successfully")
        return {
            'status': 'success',
            'route': {
                'waypoints': result['waypoints'],
                'legs': [
                    {
                        'from': result['waypoints'][i],
                        'to': result['waypoints'][i+1],
                        'distance': leg['properties']['distance'] / 1000,  # Convert to km
                        'duration': leg['properties']['time'] / 60,  # Convert to minutes
                        'geometry': leg['geometry']
                    }
                    for i, leg in enumerate(result['legs'])
                ]
            },
            'message': 'Route generated successfully'
        }
    except Exception as e:
        print(f"[LOG] Exception in generate_route: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def generate_interactive_route():
    """Generate route data for interactive web maps (GeoJSON format)."""
    print("[LOG] Starting generate_interactive_route")
    try:
        # Load waypoints from file
        with open('filtered_waypoints.json', 'r') as f:
            waypoints = json.load(f)
            
        # Create a dictionary of waypoint names
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        # Always generate a 3-day hiking route dynamically
        result = generate_hiking_route(waypoint_dict, num_days=3)
        print("[LOG] generate_hiking_route finished")
        if not result:
            print("[LOG] No valid route found")
            return {
                'status': 'error',
                'message': 'No valid route found'
            }
            
        # Export to GeoJSON for interactive maps
        geojson_data = export_route_to_geojson(result, waypoint_dict, result['scenic_midpoints'])
        
        # Format the response for interactive maps
        print("[LOG] Interactive route generated successfully")
        return {
            'status': 'success',
            'geojson': geojson_data,
            'route_summary': {
                'waypoints': result['waypoints'],
                'total_distance_km': sum(leg['properties']['distance'] for leg in result['legs']) / 1000,
                'total_duration_min': sum(leg['properties']['time'] for leg in result['legs']) / 60,
                'scenic_points': [mid['name'] for mid in result['scenic_midpoints'] if mid]
            },
            'message': 'Interactive route generated successfully'
        }
    except Exception as e:
        print(f"[LOG] Exception in generate_interactive_route: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def generate_cornwall_route():
    """Generate a Cornwall hiking route."""
    print("[LOG] Starting generate_cornwall_route")
    try:
        # Load Cornwall waypoints from file
        with open('cornwall_waypoints.json', 'r') as f:
            waypoints = json.load(f)
            
        # Create a dictionary of waypoint names
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        # Always generate a 3-day hiking route dynamically
        result = generate_cornwall_hiking_route(waypoint_dict, num_days=3)
        print("[LOG] generate_cornwall_hiking_route finished")
        if not result:
            print("[LOG] No valid Cornwall route found")
            return {
                'status': 'error',
                'message': 'No valid Cornwall route found'
            }
            
        # Format the response
        print("[LOG] Cornwall route generated successfully")
        return {
            'status': 'success',
            'route': {
                'waypoints': result['waypoints'],
                'legs': [
                    {
                        'from': result['waypoints'][i],
                        'to': result['waypoints'][i+1],
                        'distance': leg['properties']['distance'] / 1000,  # Convert to km
                        'duration': leg['properties']['time'] / 60,  # Convert to minutes
                        'geometry': leg['geometry']
                    }
                    for i, leg in enumerate(result['legs'])
                ]
            },
            'message': 'Cornwall route generated successfully'
        }
    except Exception as e:
        print(f"[LOG] Exception in generate_cornwall_route: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

def generate_cornwall_interactive_route():
    """Generate Cornwall route data for interactive web maps (GeoJSON format)."""
    print("[LOG] Starting generate_cornwall_interactive_route")
    try:
        # Load Cornwall waypoints from file
        with open('cornwall_waypoints.json', 'r') as f:
            waypoints = json.load(f)
            
        # Create a dictionary of waypoint names
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
        
        # Always generate a 3-day hiking route dynamically
        result = generate_cornwall_hiking_route(waypoint_dict, num_days=3)
        print("[LOG] generate_cornwall_hiking_route finished")
        if not result:
            print("[LOG] No valid Cornwall route found")
            return {
                'status': 'error',
                'message': 'No valid Cornwall route found'
            }
            
        # Export to GeoJSON for interactive maps
        geojson_data = export_cornwall_route_to_geojson(result, waypoint_dict, result['scenic_midpoints'])
        
        # Format the response for interactive maps
        print("[LOG] Cornwall interactive route generated successfully")
        return {
            'status': 'success',
            'geojson': geojson_data,
            'route_summary': {
                'waypoints': result['waypoints'],
                'total_distance_km': sum(leg['properties']['distance'] for leg in result['legs']) / 1000,
                'total_duration_min': sum(leg['properties']['time'] for leg in result['legs']) / 60,
                'scenic_points': [mid['name'] for mid in result['scenic_midpoints'] if mid]
            },
            'message': 'Cornwall interactive route generated successfully'
        }
    except Exception as e:
        print(f"[LOG] Exception in generate_cornwall_interactive_route: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
