import requests
import random
import matplotlib.pyplot as plt
import contextily as ctx
from pyproj import Transformer
import json
from geopy.distance import geodesic
import numpy as np
from functools import lru_cache
import os
from datetime import datetime, timedelta
import base64
from io import BytesIO
import traceback
import logging

API_KEY = "01c9293b314a49979b45d9e0a5570a3f"
# Lake District bounding box: west,south,east,north
BBOX = "-3.3,54.2,-2.7,54.6"

# Cache directory setup
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_feasible_pairs():
    """Get or compute feasible pairs between waypoints."""
    cache_file = os.path.join(CACHE_DIR, "feasible_pairs.json")
    
    # Check if cache is valid (less than 24 hours old)
    if os.path.exists(cache_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age < timedelta(hours=24):
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    # Load waypoints
    with open('filtered_waypoints.json', 'r') as f:
        waypoints = json.load(f)
    
    # Create a dictionary of coordinates
    coords = {}
    for wp in waypoints:
        name = wp['properties']['name']
        coords[name] = (wp['geometry']['coordinates'][1], wp['geometry']['coordinates'][0])
    
    # Calculate distances between all pairs
    feasible_pairs = []
    for wp1 in coords:
        for wp2 in coords:
            if wp1 != wp2:
                dist = geodesic(coords[wp1], coords[wp2]).kilometers
                # Include pairs that are between 5km and 15km apart (inclusive)
                if 5 <= dist <= 15:
                    feasible_pairs.append({
                        'from': wp1,
                        'to': wp2,
                        'distance': dist
                    })
    
    # Cache the results
    with open(cache_file, 'w') as f:
        json.dump(feasible_pairs, f)
    
    return feasible_pairs

@lru_cache(maxsize=100)
def get_scenic_points():
    """Fetch and cache scenic points."""
    cache_file = os.path.join(CACHE_DIR, "scenic_points.json")
    
    # Check if cache is valid (less than 24 hours old)
    if os.path.exists(cache_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age < timedelta(hours=24):
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    # Fetch new data
    scenic_url = f"https://api.geoapify.com/v2/places?categories=natural.mountain.peak,tourism.attraction.viewpoint&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
    scenic_resp = requests.get(scenic_url)
    scenic_data = scenic_resp.json()
    
    if 'features' not in scenic_data:
        raise Exception("Error in Scenic API response")
    
    # Process and cache the data
    scenic_info = []
    for s in scenic_data['features']:
        name = s['properties'].get('name', 'Unnamed Point')
        categories = s['properties'].get('categories', [])
        scenic_type = 'Peak' if 'natural.mountain.peak' in categories else 'Viewpoint'
        scenic_info.append({
            'name': name,
            'type': scenic_type,
            'coords': (s['geometry']['coordinates'][1], s['geometry']['coordinates'][0])
        })
    
    with open(cache_file, 'w') as f:
        json.dump(scenic_info, f)
    
    return scenic_info

def get_route(start, end):
    """
    Get route between two points using Geoapify API.
    
    Args:
        start (dict): Start coordinates with 'lat' and 'lon' keys
        end (dict): End coordinates with 'lat' and 'lon' keys
        
    Returns:
        dict: Route information including distance, duration, and surface breakdown
    """
    try:
        # Format coordinates for Geoapify API
        start_str = f"{start['lon']},{start['lat']}"
        end_str = f"{end['lon']},{end['lat']}"
        
        url = f"https://api.geoapify.com/v1/routing?waypoints={start_str}|{end_str}&mode=hike&apiKey={API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            logging.error(f"Error getting route: {response.status_code}")
            return None
            
        data = response.json()
        
        if not data.get('features'):
            logging.error("No route found")
            return None
            
        route = data['features'][0]
        properties = route['properties']
        
        # Calculate surface type percentages
        surface_percentages = {}
        total_distance = properties['distance']
        
        for segment in properties.get('segments', []):
            surface_type = segment.get('surface', 'unknown')
            segment_distance = segment.get('distance', 0)
            percentage = (segment_distance / total_distance) * 100 if total_distance > 0 else 0
            
            if surface_type not in surface_percentages:
                surface_percentages[surface_type] = 0
            surface_percentages[surface_type] += percentage
        
        return {
            'distance': properties['distance'],
            'duration': properties['time'],
            'surface_breakdown': surface_percentages,
            'geometry': route['geometry']
        }
        
    except Exception as e:
        logging.error(f"Error in get_route: {str(e)}")
        return None

def calculate_route_overlap(leg1, leg2):
    """Calculate overlap between two route legs."""
    def extract_coords(geometry):
        coords = []
        if geometry['type'] == 'LineString':
            coords = [tuple(map(float, pt)) for pt in geometry['coordinates']]
        elif geometry['type'] == 'MultiLineString':
            for line in geometry['coordinates']:
                coords.extend([tuple(map(float, pt)) for pt in line])
        return set(coords)

    coords1 = extract_coords(leg1['geometry'])
    coords2 = extract_coords(leg2['geometry'])
    # Calculate overlap
    overlap = len(coords1 & coords2) / max(1, min(len(coords1), len(coords2)))
    return overlap

def get_waypoint_score(waypoint_name):
    """Calculate a score for a waypoint based on its location and surrounding terrain."""
    # Areas known to have good hiking trails
    hiking_hotspots = {
        'Grasmere': 0.9,
        'Patterdale': 0.9,
        'Borrowdale': 0.9,
        'Seathwaite': 0.9,
        'Boot': 0.9,
        'Chapel Stile': 0.8,
        'Glenridding': 0.8,
        'Elterwater': 0.8,
        'Coniston': 0.7,
        'Hawkshead': 0.7,
        'Skelwith Bridge': 0.6,
        'Ambleside': 0.5,
        'Windermere': 0.4,
        'Ings': 0.4,
        'Bowland Bridge': 0.4,
        'Satterthwaite': 0.4
    }
    return hiking_hotspots.get(waypoint_name, 0.3)

def generate_route_map(route_data, waypoints, scenic_points):
    """Generate route map and return as base64 encoded image."""
    # Transform coordinates
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    
    # Transform route coordinates
    all_coords = [pt for leg in route_data['legs'] for pt in leg['coords']]
    lats, lons = zip(*all_coords)
    x, y = transformer.transform(lons, lats)
    
    # Transform waypoint coordinates
    waypoint_x, waypoint_y = transformer.transform(
        [p['geometry']['coordinates'][0] for p in waypoints],
        [p['geometry']['coordinates'][1] for p in waypoints]
    )
    
    # Transform scenic point coordinates
    scenic_x = []
    scenic_y = []
    scenic_names = []
    for scenic_point in scenic_points:
        if scenic_point:
            sx, sy = transformer.transform(
                [scenic_point['coords'][1]],
                [scenic_point['coords'][0]]
            )
            scenic_x.extend(sx)
            scenic_y.extend(sy)
            scenic_names.append(scenic_point['name'])
    
    # Create plot
    plt.figure(figsize=(12, 10))
    plt.plot(x, y, 'r-', label='Route')
    
    # Add direction arrows
    for i in range(0, len(x)-1, max(1, len(x)//20)):
        plt.arrow(x[i], y[i], x[i+1]-x[i], y[i+1]-y[i], 
                 shape='full', lw=0, length_includes_head=True, 
                 head_width=100, color='orange', alpha=0.5)
    
    # Plot waypoints
    colors = ['blue', 'green', 'purple', 'orange']
    for i, (wx, wy) in enumerate(zip(waypoint_x, waypoint_y)):
        if i == 0:
            label = f'Day 1 Start'
        elif i == len(waypoint_x)-1:
            label = f'Day {len(waypoint_x)-1} End'
        else:
            label = f'Day {i} End / Day {i+1} Start'
        plt.scatter(wx, wy, c=colors[i%len(colors)], s=120, marker='o', 
                   label=label, edgecolor='black', zorder=5)
        plt.text(wx, wy, waypoints[i]['properties']['name'], 
                fontsize=10, weight='bold', verticalalignment='bottom')
    
    # Plot scenic points
    if scenic_x:
        plt.scatter(scenic_x, scenic_y, c='red', s=100, marker='^', 
                   label='Scenic Points', edgecolor='black', zorder=5)
        for sx, sy, name in zip(scenic_x, scenic_y, scenic_names):
            plt.text(sx, sy, name, fontsize=8, color='red', 
                    verticalalignment='bottom')
    
    plt.title('Hiking Route (Geoapify)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend()
    
    # Add basemap
    ax = plt.gca()
    ctx.add_basemap(ax, crs="epsg:3857", source=ctx.providers.OpenStreetMap.Mapnik)
    ax.set_aspect('equal')
    
    # Save to buffer and convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def get_waypoint_coords(waypoints, name):
    print(f"[DEBUG] waypoints type: {type(waypoints)}")
    if isinstance(waypoints, dict):
        items = waypoints.values()
    else:
        items = waypoints
    for p in items:
        if isinstance(p, dict) and 'properties' in p and p['properties'].get('name') == name:
            return p['geometry']['coordinates']
    return None

def generate_hiking_route(waypoints, num_days=3, max_attempts=200, max_overlap=0.3):
    """
    Generate a hiking route through the Lake District.
    
    Args:
        waypoints (dict): Dictionary of waypoints with their coordinates
        num_days (int): Number of days for the route
        max_attempts (int): Maximum number of attempts to find a valid route
        max_overlap (float): Maximum allowed overlap between routes
        
    Returns:
        dict: Route information including waypoints, legs, and surface information
    """
    # Get scenic points
    scenic_points = get_scenic_points()
    if not scenic_points:
        logging.error("No scenic points found")
        return None
        
    # Sort scenic points by elevation
    scenic_points.sort(key=lambda x: x.get('elevation', 0), reverse=True)
    
    best_route = None
    best_score = float('inf')
    
    for attempt in range(max_attempts):
        try:
            # Generate route for each day
            daily_routes = []
            total_distance = 0
            total_duration = 0
            total_paved_percentage = 0
            total_legs = 0
            
            for day in range(num_days):
                # Get start and end waypoints for this day
                start = list(waypoints.keys())[day]
                end = list(waypoints.keys())[(day + 1) % len(waypoints)]
                
                # Find a scenic midpoint between start and end
                start_coords = waypoints[start]
                end_coords = waypoints[end]
                
                # Find the closest scenic point to the midpoint between start and end
                midpoint = {
                    'lat': (start_coords['lat'] + end_coords['lat']) / 2,
                    'lon': (start_coords['lon'] + end_coords['lon']) / 2
                }
                
                # Find the closest scenic point to the midpoint
                closest_scenic = None
                min_distance = float('inf')
                
                for point in scenic_points:
                    point_coords = {
                        'lat': point['coords'][0],
                        'lon': point['coords'][1]
                    }
                    distance = calculate_distance(midpoint, point_coords)
                    if distance < min_distance:
                        min_distance = distance
                        closest_scenic = point
                
                if not closest_scenic:
                    logging.error(f"No scenic midpoint found between {start} and {end}")
                    continue
                
                # Generate route from start to scenic midpoint
                start_to_mid = get_route(start_coords, {
                    'lat': closest_scenic['coords'][0],
                    'lon': closest_scenic['coords'][1]
                })
                
                if not start_to_mid:
                    logging.error(f"No route from {start} to scenic midpoint {closest_scenic['name']}")
                    continue
                
                # Generate route from scenic midpoint to end
                mid_to_end = get_route({
                    'lat': closest_scenic['coords'][0],
                    'lon': closest_scenic['coords'][1]
                }, end_coords)
                
                if not mid_to_end:
                    logging.error(f"No route from scenic midpoint {closest_scenic['name']} to {end}")
                    continue
                
                # Combine the routes
                day_route = {
                    'start': start,
                    'end': end,
                    'scenic_midpoint': closest_scenic['name'],
                    'legs': [
                        {
                            'start': start,
                            'end': closest_scenic['name'],
                            'distance': start_to_mid['distance'],
                            'duration': start_to_mid['duration'],
                            'surface_breakdown': start_to_mid['surface_breakdown']
                        },
                        {
                            'start': closest_scenic['name'],
                            'end': end,
                            'distance': mid_to_end['distance'],
                            'duration': mid_to_end['duration'],
                            'surface_breakdown': mid_to_end['surface_breakdown']
                        }
                    ]
                }
                
                # Calculate paved road percentage for this day
                day_paved_percentage = 0
                day_total_distance = 0
                
                for leg in day_route['legs']:
                    leg_distance = leg['distance']
                    day_total_distance += leg_distance
                    paved_percentage = leg['surface_breakdown'].get('paved_smooth', 0)
                    day_paved_percentage += (paved_percentage * leg_distance)
                
                day_paved_percentage = (day_paved_percentage / day_total_distance) if day_total_distance > 0 else 0
                
                # Check if paved road percentage is within limit
                if day_paved_percentage > 35:
                    logging.info(f"Day {day + 1} route rejected: {day_paved_percentage:.2f}% paved roads")
                    continue
                
                daily_routes.append(day_route)
                total_distance += day_total_distance
                total_duration += sum(leg['duration'] for leg in day_route['legs'])
                total_paved_percentage += day_paved_percentage
                total_legs += len(day_route['legs'])
            
            if len(daily_routes) == num_days:
                # Calculate average paved road percentage
                avg_paved_percentage = total_paved_percentage / num_days
                
                # Calculate route score (lower is better)
                route_score = (
                    total_distance * 0.4 +  # Distance weight
                    total_duration * 0.3 +  # Duration weight
                    avg_paved_percentage * 0.3  # Paved road percentage weight
                )
                
                logging.info(f"Route found - Score: {route_score:.2f}, Paved: {avg_paved_percentage:.2f}%")
                
                if route_score < best_score:
                    best_score = route_score
                    best_route = {
                        'days': daily_routes,
                        'total_distance': total_distance,
                        'total_duration': total_duration,
                        'avg_paved_percentage': avg_paved_percentage
                    }
                    
                    # If we have a good enough route, return it
                    if route_score < 1000:  # Adjust this threshold as needed
                        break
        
        except Exception as e:
            logging.error(f"Error generating route: {str(e)}")
            continue
    
    if best_route:
        # Generate route map
        route_map = generate_route_map(best_route, waypoints, scenic_points)
        best_route['map'] = route_map
        
        return best_route
    
    return None

if __name__ == "__main__":
    # Example usage
    result = generate_hiking_route()
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("\nHiking Itinerary (Lake District, Geoapify-only)")
        print("=" * 50)
        for day in result['route']:
            print(f"\nDay {day['day']}: {day['start']} → {day['end']}")
            print(f"Distance: {day['distance']} km")
            if 'scenic_detour' in day:
                print(f"Scenic Detour: {day['scenic_detour']['name']} ({day['scenic_detour']['type']})")
        print("\n" + "=" * 50)
        print("\nRoute map saved as geoapify_route.png") 