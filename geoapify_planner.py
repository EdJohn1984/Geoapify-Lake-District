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
                if 10 <= dist <= 15:
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
        lon, lat = s['geometry']['coordinates'][0], s['geometry']['coordinates'][1]
        scenic_info.append({
            'name': name,
            'type': scenic_type,
            'coords': [lon, lat]
        })
    
    with open(cache_file, 'w') as f:
        json.dump(scenic_info, f)
    
    return scenic_info

def get_route(start, end, midpoint=None):
    """Get route between two waypoints, optionally via a midpoint."""
    # Get coordinates for waypoints
    with open('filtered_waypoints.json', 'r') as f:
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

def find_best_scenic_midpoint(start_coords, end_coords, scenic_points):
    """Find the best scenic midpoint between two coordinates."""
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

def generate_route_map(route_data, waypoints, scenic_points):
    """Generate route map and return as base64 encoded image."""
    # Transform coordinates
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    
    # Transform route coordinates
    all_coords = [pt for leg in route_data['legs'] for pt in leg['coords']]
    lats, lons = zip(*all_coords)
    x, y = transformer.transform(lons, lats)
    
    # Fixed bounding box for Lake District in EPSG:4326 (lon/lat):
    bbox_wgs84 = (-3.3, 54.2, -2.7, 54.6)
    bbox_x0, bbox_y0 = transformer.transform(bbox_wgs84[0], bbox_wgs84[1])
    bbox_x1, bbox_y1 = transformer.transform(bbox_wgs84[2], bbox_wgs84[3])
    min_x, max_x = min(bbox_x0, bbox_x1), max(bbox_x0, bbox_x1)
    min_y, max_y = min(bbox_y0, bbox_y1), max(bbox_y0, bbox_y1)
    
    # Create a name-to-waypoint dictionary for lookup
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
    # Transform route waypoints
    route_waypoints = [waypoint_dict[name] for name in route_data['waypoints']]
    route_waypoint_x, route_waypoint_y = transformer.transform(
        [p['geometry']['coordinates'][0] for p in route_waypoints],
        [p['geometry']['coordinates'][1] for p in route_waypoints]
    )
    
    # Transform all waypoints
    all_waypoint_x, all_waypoint_y = transformer.transform(
        [wp['geometry']['coordinates'][0] for wp in waypoints],
        [wp['geometry']['coordinates'][1] for wp in waypoints]
    )
    
    # Transform all scenic points
    scenic_x = []
    scenic_y = []
    scenic_names = []
    for idx, scenic_point in enumerate(scenic_points):
        if scenic_point:
            lat, lon = scenic_point['coords']
            if idx < 10:
                print(f"Scenic point {idx}: lat={lat}, lon={lon}")
            sx, sy = transformer.transform([lon], [lat])
            if idx < 10:
                print(f"  transformer.transform output: sx={sx}, sy={sy}, type(sx)={type(sx)}, type(sy)={type(sy)}, len(sx)={len(sx)}, len(sy)={len(sy)}")
            scenic_x.extend(sx)
            scenic_y.extend(sy)
            scenic_names.append(scenic_point['name'])
    # Print debug info for scenic points
    print("First 10 transformed scenic points (x, y):")
    for i in range(min(10, len(scenic_x))):
        print(f"{scenic_names[i]}: x={scenic_x[i]}, y={scenic_y[i]}")
    if scenic_x and scenic_y:
        print(f"scenic_x range: {min(scenic_x)} to {max(scenic_x)}")
        print(f"scenic_y range: {min(scenic_y)} to {max(scenic_y)}")
    else:
        print("No scenic points to plot after transformation.")
    
    # Create plot
    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    
    # Plot all waypoints
    plt.scatter(all_waypoint_x, all_waypoint_y, c='deepskyblue', s=40, marker='o', label='All Waypoints', edgecolor='black', zorder=2)
    
    # Plot all scenic points
    if scenic_x:
        plt.scatter(scenic_x, scenic_y, c='red', s=60, marker='^', label='All Scenic Points', edgecolor='black', zorder=3)
    
    # Plot route path with enhanced visibility
    plt.plot(x, y, 'b-', label='Hiking Route', linewidth=4, alpha=0.8, zorder=4)
    print(f"[LOG] Plotting route path with {len(x)} coordinate points")
    
    # Plot individual day segments with different colors for better visibility
    day_colors = ['red', 'green', 'purple', 'orange', 'brown']
    coord_start = 0
    for i, leg in enumerate(route_data['legs']):
        leg_coords = leg['coords']
        leg_x, leg_y = zip(*leg_coords)
        leg_x_transformed, leg_y_transformed = transformer.transform(leg_x, leg_y)
        color = day_colors[i % len(day_colors)]
        plt.plot(leg_x_transformed, leg_y_transformed, color=color, linewidth=2, alpha=0.6, 
                label=f'Day {i+1} Path' if i < 3 else None, zorder=3)
        print(f"[LOG] Day {i+1} segment: {len(leg_coords)} points, color: {color}")
    
    # Plot route waypoints (start, mid, end)
    colors = ['blue', 'green', 'purple', 'orange']
    for i, (wx, wy) in enumerate(zip(route_waypoint_x, route_waypoint_y)):
        if i == 0:
            label = f'Day 1 Start'
        elif i == len(route_waypoint_x)-1:
            label = f'Day {len(route_waypoint_x)-1} End'
        else:
            label = f'Day {i} End / Day {i+1} Start'
        plt.scatter(wx, wy, c=colors[i%len(colors)], s=120, marker='o', 
                   label=label if i < 3 else None, edgecolor='black', zorder=5)
        plt.text(wx, wy, route_waypoints[i]['properties']['name'], 
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
        
        plt.scatter(mid_x, mid_y, c='gold', s=180, marker='*', 
                   label='Scenic Midpoints', edgecolor='black', zorder=7)
        for mx, my, name in zip(mid_x, mid_y, mid_names):
            plt.text(mx, my, name, fontsize=9, color='darkgoldenrod', 
                    verticalalignment='bottom', weight='bold', zorder=8)
    
    # Set axis limits first
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect('equal')
    
    # Add basemap
    try:
        ctx.add_basemap(ax, crs="epsg:3857", source=ctx.providers.OpenStreetMap.Mapnik, alpha=0.8)
        print("[LOG] OpenStreetMap basemap added successfully")
    except Exception as e:
        print(f"[LOG] Basemap error: {e}")
        # Fallback: try with different provider
        try:
            ctx.add_basemap(ax, crs="epsg:3857", source=ctx.providers.CartoDB.Positron, alpha=0.8)
            print("[LOG] CartoDB Positron basemap added as fallback")
        except Exception as e2:
            print(f"[LOG] Fallback basemap also failed: {e2}")
    
    plt.title('Hiking Route (Geoapify)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend(loc='upper left', fontsize=9)
    
    # Save to buffer and convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return image_base64

def export_route_to_geojson(route_data, waypoints, scenic_midpoints):
    """Export route data as GeoJSON for interactive web maps."""
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    # Add route waypoints
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
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
    
    # Add route legs as LineString features
    for i, leg in enumerate(route_data['legs']):
        feature = {
            "type": "Feature",
            "properties": {
                "day": i + 1,
                "distance_km": round(leg['properties']['distance'] / 1000, 1),
                "duration_min": round(leg['properties']['time'] / 60, 0),
                "type": "route_leg",
                "color": ["red", "green", "purple", "orange", "brown"][i % 5],
                "description": f"Day {i + 1}: {leg['properties']['distance']/1000:.1f}km, {leg['properties']['time']/60:.0f}min"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": leg['coords']
            }
        }
        geojson["features"].append(feature)
    
    # Add scenic midpoints
    for i, midpoint in enumerate(scenic_midpoints):
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

def extract_coords_from_geometry(geometry):
    coords = []
    if geometry['type'] == 'LineString':
        coords = [tuple(map(float, pt)) for pt in geometry['coordinates']]
    elif geometry['type'] == 'MultiLineString':
        for line in geometry['coordinates']:
            coords.extend([tuple(map(float, pt)) for pt in line])
    return coords

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
    
    # Get scenic points
    scenic_points = get_scenic_points()
    print(f"[LOG] Found {len(scenic_points)} scenic points")
    
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
            midpoint = find_best_scenic_midpoint(current_coords, next_coords, scenic_points)
            
            # Get route between current and next point, via midpoint if available
            route_data = get_route(current, next_point, midpoint)
            if not route_data:
                print(f"[LOG]  No route found between {current} and {next_point}")
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