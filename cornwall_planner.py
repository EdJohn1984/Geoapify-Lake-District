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
# Cornwall bounding box: west,south,east,north
BBOX = "-5.7,49.8,-4.0,50.9"

# Cache directory setup
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cornwall_feasible_pairs():
    """Get or compute feasible pairs between Cornwall waypoints."""
    cache_file = os.path.join(CACHE_DIR, "cornwall_feasible_pairs.json")
    
    # Check if cache is valid (less than 24 hours old)
    if os.path.exists(cache_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age < timedelta(hours=24):
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    # Load Cornwall waypoints
    with open('cornwall_waypoints.json', 'r') as f:
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
                # Cornwall may need slightly different distance ranges due to coastal geography
                if 8 <= dist <= 18:  # Slightly wider range for Cornwall
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
def get_cornwall_scenic_points():
    """Fetch and cache scenic points for Cornwall."""
    cache_file = os.path.join(CACHE_DIR, "cornwall_scenic_points.json")
    
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
        lon, lat = s['geometry']['coordinates'][0], s['geometry']['coordinates'][1]
        scenic_info.append({
            'name': name,
            'type': scenic_type,
            'coords': [lon, lat]
        })
    
    with open(cache_file, 'w') as f:
        json.dump(scenic_info, f)
    
    return scenic_info

def get_cornwall_route(start, end, midpoint=None):
    """Get route between two Cornwall waypoints, optionally via a midpoint."""
    # Get coordinates for waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints = json.load(f)
        
    start_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == start), None)
    end_coords = next((p['geometry']['coordinates'] for p in waypoints if p['properties']['name'] == end), None)
    
    if not start_coords or not end_coords:
        return None
    
    # If no midpoint, get direct route
    if not midpoint:
        wp_str = f"{start_coords[1]},{start_coords[0]}|{end_coords[1]},{end_coords[0]}"
    else:
        # Get midpoint coordinates
        mid_coords = (midpoint['coords'][0], midpoint['coords'][1])
        wp_str = f"{start_coords[1]},{start_coords[0]}|{mid_coords[1]},{mid_coords[0]}|{end_coords[1]},{end_coords[0]}"
    
    # Construct URL
    url = f"https://api.geoapify.com/v1/routing?waypoints={wp_str}&mode=hike&apiKey={API_KEY}"
    
    # Make request
    response = requests.get(url)
    if response.status_code != 200:
        return None
        
    data = response.json()
    if not data['features']:
        return None
        
    # Return both properties and geometry
    return {
        'properties': data['features'][0]['properties'],
        'geometry': data['features'][0]['geometry']
    }

def calculate_route_overlap(leg1, leg2):
    """Calculate overlap between two route legs."""
    coords1 = leg1.get('coords', [])
    coords2 = leg2.get('coords', [])
    
    if not coords1 or not coords2:
        return 0
    
    # Convert to sets of coordinate tuples for comparison
    set1 = set(tuple(coord) for coord in coords1)
    set2 = set(tuple(coord) for coord in coords2)
    
    # Calculate overlap as intersection over union
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0
    
    overlap = intersection / union
    return overlap

def find_best_cornwall_scenic_midpoint(start_coords, end_coords, scenic_points):
    """Find the best scenic midpoint between two coordinates for Cornwall."""
    if not scenic_points:
        return None
        
    # Calculate midpoint between start and end
    mid_lat = (start_coords[0] + end_coords[0]) / 2
    mid_lon = (start_coords[1] + end_coords[1]) / 2
    
    # Find scenic points within 10km of the midpoint
    best_point = None
    min_distance = float('inf')
    
    for point in scenic_points:
        dist = geodesic((mid_lat, mid_lon), point['coords']).kilometers
        if dist < 10 and dist < min_distance:  # Within 10km and closer than previous best
            best_point = point
            min_distance = dist
    
    if not best_point:
        print(f"[LOG] No scenic midpoint found within 10km of midpoint ({mid_lat}, {mid_lon})")
    
    return best_point

def extract_coords_from_geometry(geometry):
    """Extract coordinates from GeoJSON geometry."""
    coords = []
    if geometry['type'] == 'LineString':
        coords.extend([tuple(map(float, pt)) for pt in geometry['coordinates']])
    elif geometry['type'] == 'MultiLineString':
        for line in geometry['coordinates']:
            coords.extend([tuple(map(float, pt)) for pt in line])
    return coords

def generate_cornwall_hiking_route(waypoints, num_days=3, max_tries=200, good_enough_threshold=0.1):
    """
    Generate a hiking route through Cornwall waypoints with scenic midpoints.
    
    Args:
        waypoints: Dictionary of waypoint data
        num_days: Number of days for the route
        max_tries: Maximum number of attempts to find a route
        good_enough_threshold: If a route has a score below this threshold, return it immediately
    """
    print("[LOG] Starting Cornwall route generation")
    
    # Get feasible pairs for route generation
    feasible_pairs = get_cornwall_feasible_pairs()
    if not feasible_pairs:
        print("[LOG] No feasible pairs found")
        return None
        
    print(f"[LOG] Found {len(feasible_pairs)} feasible pairs")
    
    # Get scenic points
    scenic_points = get_cornwall_scenic_points()
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
        
        # Start with a random waypoint that has feasible next steps
        valid_starts = [wp for wp in waypoints.keys() if wp in feasible_next_steps]
        if not valid_starts:
            print("[LOG] No valid starting points found")
            break
            
        current = random.choice(valid_starts)
        route = [current]
        used_waypoints = {current}
        route_legs = []
        scenic_midpoints = []
        
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
            
            # Get coordinates for current and next point
            current_coords = waypoints[current]['geometry']['coordinates']
            next_coords = waypoints[next_point]['geometry']['coordinates']
            
            # Find scenic midpoint
            midpoint = find_best_cornwall_scenic_midpoint(current_coords, next_coords, scenic_points)
            
            # Get route between current and next point, via midpoint if available
            route_data = get_cornwall_route(current, next_point, midpoint)
            if not route_data:
                print(f"[LOG]  No route found from {current} to {next_point}")
                break
            
            # Add 'coords' key for mapping
            route_data['coords'] = extract_coords_from_geometry(route_data['geometry'])
            
            # Add to route
            route.append(next_point)
            used_waypoints.add(next_point)
            route_legs.append(route_data)
            if midpoint:
                scenic_midpoints.append(midpoint)
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
                    'legs': route_legs,
                    'scenic_midpoints': scenic_midpoints
                }
                print(f"[LOG] New best Cornwall itinerary found with score {score:.3f}")
                
                # If we found a route that's good enough, return it immediately
                if score <= good_enough_threshold:
                    print(f"[LOG] Found route with score {score:.3f} below threshold {good_enough_threshold}")
                    return best_route
    
    if best_route:
        print(f"[LOG] Found valid Cornwall route with score {best_score:.3f}")
        return best_route
    else:
        print("[LOG] No valid Cornwall route found")
        return None

def generate_cornwall_route_map(route_data, waypoints, scenic_points):
    """Generate route map for Cornwall and return as base64 encoded image."""
    if not route_data or not route_data.get('legs'):
        return None
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Transformer for converting lat/lon to Web Mercator
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    
    # Plot each route leg
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    all_x, all_y = [], []
    
    for i, leg in enumerate(route_data['legs']):
        if 'coords' in leg and leg['coords']:
            coords = leg['coords']
            lons = [coord[0] for coord in coords]
            lats = [coord[1] for coord in coords]
            
            # Transform to Web Mercator
            x, y = transformer.transform(lons, lats)
            all_x.extend(x)
            all_y.extend(y)
            
            # Plot the route
            ax.plot(x, y, color=colors[i % len(colors)], linewidth=3, 
                   label=f'Day {i+1}', alpha=0.8)
    
    if not all_x or not all_y:
        return None
    
    # Set plot bounds
    margin = 0.01
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    # Plot waypoints
    route_waypoints = []
    for wp_name in route_data['waypoints']:
        wp_data = waypoints.get(wp_name)
        if wp_data:
            route_waypoints.append(wp_data)
    
    if route_waypoints:
        route_waypoint_lons = [wp['geometry']['coordinates'][0] for wp in route_waypoints]
        route_waypoint_lats = [wp['geometry']['coordinates'][1] for wp in route_waypoints]
        route_waypoint_x, route_waypoint_y = transformer.transform(route_waypoint_lons, route_waypoint_lats)
        
        # Plot route waypoints
        colors = ['blue', 'green', 'purple', 'orange']
        for i, (wx, wy) in enumerate(zip(route_waypoint_x, route_waypoint_y)):
            if i == 0:
                label = f'Day 1 Start'
            elif i == len(route_waypoint_x)-1:
                label = f'Day {len(route_waypoint_x)-1} End'
            else:
                label = f'Day {i} End / Day {i+1} Start'
            ax.scatter(wx, wy, c=colors[i%len(colors)], s=120, marker='o', 
                     label=label if i < 3 else None, edgecolor='black', zorder=5)
            ax.text(wx, wy, route_waypoints[i]['properties']['name'], 
                    fontsize=10, weight='bold', verticalalignment='bottom', zorder=6)
    
    # Plot scenic midpoints if available
    if 'scenic_midpoints' in route_data and route_data['scenic_midpoints']:
        mid_x = []
        mid_y = []
        mid_names = []
        for midpoint in route_data['scenic_midpoints']:
            lon, lat = midpoint['coords'][0], midpoint['coords'][1]
            mx, my = transformer.transform([lon], [lat])
            mid_x.extend(mx)
            mid_y.extend(my)
            mid_names.append(f"{midpoint['name']} ({midpoint['type']})")
        
        ax.scatter(mid_x, mid_y, c='gold', s=180, marker='*', 
                 label='Scenic Midpoints', edgecolor='black', zorder=7)
        for mx, my, name in zip(mid_x, mid_y, mid_names):
            ax.text(mx, my, name, fontsize=9, color='darkgoldenrod', 
                    verticalalignment='bottom', weight='bold', zorder=8)
    
    ax.set_title('Cornwall Hiking Route')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.legend(loc='upper left', fontsize=9)
    
    # Add basemap
    try:
        ctx.add_basemap(ax, crs="epsg:3857", source=ctx.providers.OpenStreetMap.Mapnik)
    except Exception as e:
        print(f"[LOG] Basemap error: {e}")
    
    ax.set_aspect('equal')
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    
    # Save to buffer and convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def export_cornwall_route_to_geojson(route_data, waypoints, scenic_midpoints):
    """Export Cornwall route to GeoJSON format."""
    features = []
    
    # Add route legs
    for i, leg in enumerate(route_data['legs']):
        feature = {
            "type": "Feature",
            "properties": {
                "name": f"Day {i+1}",
                "from": route_data['waypoints'][i],
                "to": route_data['waypoints'][i+1],
                "distance_km": leg['properties']['distance'] / 1000,
                "duration_min": leg['properties']['time'] / 60
            },
            "geometry": leg['geometry']
        }
        features.append(feature)
    
    # Add waypoints
    for wp_name in route_data['waypoints']:
        wp_data = waypoints.get(wp_name)
        if wp_data:
            feature = {
                "type": "Feature",
                "properties": {
                    "name": wp_name,
                    "type": "waypoint"
                },
                "geometry": wp_data['geometry']
            }
            features.append(feature)
    
    # Add scenic midpoints
    for i, midpoint in enumerate(scenic_midpoints):
        if midpoint:
            feature = {
                "type": "Feature",
                "properties": {
                    "name": midpoint['name'],
                    "type": "scenic_midpoint",
                    "scenic_type": midpoint['type']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": midpoint['coords']
                }
            }
            features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

if __name__ == "__main__":
    # Example usage
    print("Testing Cornwall route generation...")
    
    # Load waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints_data = json.load(f)
    
    # Create waypoint dictionary
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints_data}
    
    # Generate route
    result = generate_cornwall_hiking_route(waypoint_dict, num_days=3)
    
    if result:
        print("\n=== Cornwall Route Generated ===")
        print(f"Waypoints: {' → '.join(result['waypoints'])}")
        print(f"Scenic midpoints: {len(result['scenic_midpoints'])}")
        
        for i, leg in enumerate(result['legs']):
            print(f"Day {i+1}: {result['waypoints'][i]} → {result['waypoints'][i+1]}")
            print(f"  Distance: {leg['properties']['distance']/1000:.1f} km")
            print(f"  Duration: {leg['properties']['time']/60:.1f} minutes")
            if i < len(result['scenic_midpoints']):
                midpoint = result['scenic_midpoints'][i]
                if midpoint:
                    print(f"  Scenic: {midpoint['name']} ({midpoint['type']})")
    else:
        print("No route could be generated")
