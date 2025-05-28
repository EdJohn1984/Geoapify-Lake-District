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
    """Get route between two waypoints, including surface type breakdown."""
    # Get coordinates for waypoints
    with open('filtered_waypoints.json', 'r') as f:
        waypoints = json.load(f)
        
    start_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == start), None)
    end_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == end), None)
    
    if not start_coords or not end_coords:
        return None
        
    # Format waypoints string
    wp_str = f"{start_coords[1]},{start_coords[0]}|{end_coords[1]},{end_coords[0]}"
    
    # Construct URL with stronger preferences for hiking trails and natural surfaces
    url = f"https://api.geoapify.com/v1/routing?waypoints={wp_str}&mode=hike&details=route_details&prefer_surface=path,dirt,gravel,compacted&avoid_surface=paved_smooth&prefer_highways=path,footway,track&avoid_highways=primary,secondary,tertiary,residential&apiKey={API_KEY}"
    
    # Make request
    response = requests.get(url)
    if response.status_code != 200:
        return None
        
    data = response.json()
    if not data['features']:
        return None
    
    # Calculate surface type percentages
    surface_distances = {}
    total_distance = 0
    try:
        legs = data['features'][0]['properties'].get('legs', [])
        for leg in legs:
            for step in leg.get('steps', []):
                surface = step.get('surface', 'unknown')
                dist = step.get('distance', 0)
                surface_distances[surface] = surface_distances.get(surface, 0) + dist
                total_distance += dist
    except Exception as e:
        # If the structure is not as expected, skip surface calculation
        surface_distances = {}
        total_distance = 0
    
    surface_percentages = {}
    if total_distance > 0:
        for surface, dist in surface_distances.items():
            surface_percentages[surface] = round(100 * dist / total_distance, 2)
    
    # Return both properties, geometry, and surface breakdown
    return {
        'properties': data['features'][0]['properties'],
        'geometry': data['features'][0]['geometry'],
        'surface_percentages': surface_percentages
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

def generate_hiking_route(waypoints, num_days=3, max_attempts=200, max_overlap=0.3):
    """
    Generate a hiking route through the Lake District.
    Dynamically creates a 3-day itinerary based on feasible pairs of waypoints.
    """
    try:
        feasible_pairs = get_feasible_pairs()
        if not feasible_pairs:
            print("[LOG] No feasible pairs found")
            return None

        scenic_points = get_scenic_points()
        if not scenic_points:
            print("[LOG] No scenic points found")
            return None

        # No elevation property in scenic_points, so skip sort by elevation
        # scenic_points.sort(key=lambda x: x.get('properties', {}).get('ele', 0), reverse=True)

        best_route = None
        best_score = float('inf')
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            route = []
            used_waypoints = set()
            total_distance = 0
            total_overlap = 0
            route_legs = []

            for day in range(num_days):
                if not feasible_pairs:
                    break
                valid_pairs = [pair for pair in feasible_pairs 
                             if pair['from'] not in used_waypoints and pair['to'] not in used_waypoints]
                if not valid_pairs:
                    break
                pair = random.choice(valid_pairs)
                start = pair['from']
                end = pair['to']
                used_waypoints.add(start)
                used_waypoints.add(end)
                start_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == start), None)
                end_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == end), None)
                if not start_coords or not end_coords:
                    print(f"[LOG] Could not find coordinates for {start} or {end}")
                    continue
                best_midpoint = None
                min_deviation = float('inf')
                for point in scenic_points:
                    mid_coords = point['coords']
                    start_to_mid = geodesic((start_coords[1], start_coords[0]), mid_coords).kilometers
                    mid_to_end = geodesic(mid_coords, (end_coords[1], end_coords[0])).kilometers
                    total_dist = geodesic((start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])).kilometers
                    if start_to_mid + mid_to_end <= total_dist * 1.5:
                        deviation = abs(start_to_mid - mid_to_end)
                        if deviation < min_deviation:
                            min_deviation = deviation
                            best_midpoint = point
                if not best_midpoint:
                    print(f"[LOG] No scenic midpoint found between {start} and {end}")
                    continue
                # Get route from start to midpoint
                start_to_mid = get_route(start, best_midpoint['name'])
                if not start_to_mid:
                    print(f"[LOG] No route from {start} to scenic midpoint {best_midpoint['name']}")
                    continue
                # Get route from midpoint to end
                mid_to_end = get_route(best_midpoint['name'], end)
                if not mid_to_end:
                    print(f"[LOG] No route from scenic midpoint {best_midpoint['name']} to {end}")
                    continue
                # Calculate paved road percentage for both legs
                def get_paved_percent(leg):
                    sp = leg.get('surface_percentages', {})
                    return sp.get('paved_smooth', 0)
                paved_percentage = (
                    get_paved_percent(start_to_mid) * start_to_mid['properties']['distance'] +
                    get_paved_percent(mid_to_end) * mid_to_end['properties']['distance']
                ) / (start_to_mid['properties']['distance'] + mid_to_end['properties']['distance'])
                if paved_percentage > 35:
                    print(f"[LOG] Route rejected: {paved_percentage:.2f}% paved roads")
                    continue
                day_legs = []
                day_legs.append({
                    'start': start,
                    'end': best_midpoint['name'],
                    'distance': start_to_mid['properties']['distance'],
                    'duration': start_to_mid['properties']['duration'],
                    'geometry': start_to_mid['geometry'],
                    'surface_breakdown': start_to_mid['surface_percentages']
                })
                day_legs.append({
                    'start': best_midpoint['name'],
                    'end': end,
                    'distance': mid_to_end['properties']['distance'],
                    'duration': mid_to_end['properties']['duration'],
                    'geometry': mid_to_end['geometry'],
                    'surface_breakdown': mid_to_end['surface_percentages']
                })
                for prev_leg in route_legs:
                    overlap = calculate_route_overlap(day_legs[0], prev_leg)
                    total_overlap += overlap
                    overlap = calculate_route_overlap(day_legs[1], prev_leg)
                    total_overlap += overlap
                route_legs.extend(day_legs)
                total_distance += start_to_mid['properties']['distance'] + mid_to_end['properties']['distance']
                route.append({
                    'day': day + 1,
                    'start': start,
                    'end': end,
                    'midpoint': best_midpoint['name'],
                    'distance': start_to_mid['properties']['distance'] + mid_to_end['properties']['distance'],
                    'duration': start_to_mid['properties']['duration'] + mid_to_end['properties']['duration'],
                    'legs': day_legs
                })
            if len(route) == num_days:
                score = total_overlap / len(route_legs) if route_legs else float('inf')
                print(f"[LOG] Route attempt {attempts}: {len(route)} days, "
                      f"total distance: {total_distance:.2f}km, "
                      f"overlap: {total_overlap:.2f}, "
                      f"score: {score:.2f}, "
                      f"paved roads: {paved_percentage:.2f}%")
                if score < best_score:
                    best_score = score
                    best_route = route
                if score < 0.1:
                    break
        if best_route:
            route_map = generate_route_map(best_route, waypoints, scenic_points)
            return {
                'route': best_route,
                'map': route_map,
                'total_distance': sum(day['distance'] for day in best_route),
                'total_duration': sum(day['duration'] for day in best_route)
            }
        return None
    except Exception as e:
        print(f"[LOG] Exception in generate_route: {e}\n{traceback.format_exc()}")
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