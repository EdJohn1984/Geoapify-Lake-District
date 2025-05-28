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
    """Get route between two waypoints."""
    # Get coordinates for waypoints
    with open('filtered_waypoints.json', 'r') as f:
        waypoints = json.load(f)
        
    start_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == start), None)
    end_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == end), None)
    
    if not start_coords or not end_coords:
        return None
        
    # Format waypoints string
    wp_str = f"{start_coords[1]},{start_coords[0]}|{end_coords[1]},{end_coords[0]}"
    
    # Construct URL with surface details
    url = f"https://api.geoapify.com/v1/routing?waypoints={wp_str}&mode=hike&details=surface&apiKey={API_KEY}"
    
    # Make request
    response = requests.get(url)
    if response.status_code != 200:
        return None
        
    data = response.json()
    if not data['features']:
        return None
        
    # Process surface information
    surface_info = {}
    if 'surface' in data['features'][0]['properties']:
        surface_details = data['features'][0]['properties']['surface']
        total_distance = data['features'][0]['properties']['distance']
        
        # Calculate percentages for each surface type
        for surface_type, distance in surface_details.items():
            percentage = (distance / total_distance) * 100
            surface_info[surface_type] = round(percentage, 1)
    
    # Return properties, geometry, and surface information
    return {
        'properties': data['features'][0]['properties'],
        'geometry': data['features'][0]['geometry'],
        'surface_info': surface_info
    }

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

def generate_hiking_route(waypoints, num_days=3, max_tries=200, good_enough_threshold=0.1):
    """Generate a hiking route through the Lake District.
    
    Args:
        waypoints: Dictionary of waypoint data
        num_days: Number of days for the route
        max_tries: Maximum number of attempts to find a route
        good_enough_threshold: If a route has a score below this threshold, return it immediately
    """
    print("[LOG] Starting route generation")
    
    # Get feasible pairs for route generation
    feasible_pairs = get_feasible_pairs()
    if not feasible_pairs:
        print("[LOG] No feasible pairs found")
        return None
        
    print(f"[LOG] Found {len(feasible_pairs)} feasible pairs")
    
    # Create lookup dictionary for faster access
    feasible_next_steps = {}
    for pair in feasible_pairs:
        start = pair['from']
        end = pair['to']
        if start not in feasible_next_steps:
            feasible_next_steps[start] = []
        feasible_next_steps[start].append(end)
    
    best_route = None
    best_score = float('inf')
    
    # Try to generate a valid route
    for attempt in range(max_tries):
        print(f"[LOG] Try {attempt + 1}/{max_tries}")
        
        # Start with a random waypoint that has feasible next steps
        valid_starts = [wp for wp in waypoints.keys() if wp in feasible_next_steps]
        if not valid_starts:
            print("[LOG] No valid starting points found")
            break
            
        current = random.choice(valid_starts)
        route = [current]
        used_waypoints = {current}
        route_legs = []
        
        # Build route day by day
        for day in range(num_days):
            print(f"[LOG]  Day {day + 1}: Generating leg from {current}")
            
            # Get possible next steps from feasible pairs
            if current not in feasible_next_steps:
                print(f"[LOG]  No feasible next steps from {current}")
                break
                
            next_steps = [next_point for next_point in feasible_next_steps[current] 
                         if next_point not in used_waypoints]
            
            if not next_steps:
                print(f"[LOG]  No unused feasible next steps from {current}")
                break
                
            # Choose a random next step from feasible options
            next_point = random.choice(next_steps)
            
            # Get route between current and next point
            route_data = get_route(current, next_point)
            if not route_data:
                print(f"[LOG]  No route found between {current} and {next_point}")
                break
                
            # Add to route
            route.append(next_point)
            used_waypoints.add(next_point)
            route_legs.append(route_data)
            current = next_point
            
        # If we have a complete route, calculate its score
        if len(route) == num_days + 1:
            # Calculate overlap between legs
            overlap = 0
            for i in range(len(route_legs) - 1):
                overlap += calculate_route_overlap(route_legs[i], route_legs[i+1])
            
            # Calculate score (lower is better)
            score = overlap / (num_days - 1)  # Average overlap per leg
            print(f"[LOG] Route score: {score:.3f}")
            
            if score < best_score:
                best_score = score
                best_route = {
                    'waypoints': route,
                    'legs': route_legs
                }
                print(f"[LOG] New best itinerary found with score {score:.3f}")
                
                # If we found a route that's good enough, return it immediately
                if score <= good_enough_threshold:
                    print(f"[LOG] Found route with score {score:.3f} below threshold {good_enough_threshold}")
                    return best_route
    
    if best_route:
        print(f"[LOG] Found valid route with score {best_score:.3f}")
        return best_route
    else:
        print("[LOG] No valid route found")
        return None

if __name__ == "__main__":
    # Example usage
    result = generate_hiking_route()
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("\nHiking Itinerary (Lake District, Geoapify-only)")
        print("=" * 50)
        for day in result['days']:
            print(f"\nDay {day['day']}: {day['start']} → {day['end']}")
            print(f"Distance: {day['distance']} km")
            if 'scenic_detour' in day:
                print(f"Scenic Detour: {day['scenic_detour']['name']} ({day['scenic_detour']['type']})")
        print("\n" + "=" * 50)
        print("\nRoute map saved as geoapify_route.png") 