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
        scenic_info.append({
            'name': name,
            'type': scenic_type,
            'coords': (s['geometry']['coordinates'][1], s['geometry']['coordinates'][0])
        })
    
    with open(cache_file, 'w') as f:
        json.dump(scenic_info, f)
    
    return scenic_info

@lru_cache(maxsize=1000)
def get_route(waypoints_str):
    """Get route between waypoints with caching."""
    url = f"https://api.geoapify.com/v1/routing?waypoints={waypoints_str}&mode=hike&apiKey={API_KEY}"
    resp = requests.get(url)
    return resp.json()

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

def generate_hiking_route(num_days=3, num_tries=200):
    print(f"[LOG] Starting generate_hiking_route with num_days={num_days}, num_tries={num_tries}")
    try:
        # Load waypoints
        print("[LOG] Loading waypoints from filtered_waypoints.json")
        with open('filtered_waypoints.json', 'r') as f:
            places = json.load(f)
        print(f"[LOG] Loaded {len(places)} waypoints")
        
        # Get feasible pairs
        print("[LOG] Getting feasible pairs")
        feasible_pairs = get_feasible_pairs()
        print(f"[LOG] Found {len(feasible_pairs)} feasible pairs")
        
        # Create a lookup dictionary for faster access
        feasible_lookup = {}
        for pair in feasible_pairs:
            if pair['from'] not in feasible_lookup:
                feasible_lookup[pair['from']] = []
            feasible_lookup[pair['from']].append(pair['to'])
        
        # Get scenic points
        print("[LOG] Fetching scenic points")
        scenic_info = get_scenic_points()
        print(f"[LOG] Got {len(scenic_info)} scenic points")
        
        best_itinerary = None
        best_score = float('inf')
        best_result = None
        best_scenic_points = None
        
        for try_num in range(num_tries):
            print(f"[LOG] Try {try_num+1}/{num_tries}")
            
            # Generate a valid route using feasible pairs
            route = []
            used_places = set()
            
            # Start with a random place
            start = random.choice(list(feasible_lookup.keys()))
            route.append(start)
            used_places.add(start)
            
            # Build the route using feasible pairs
            valid_route = True
            for day in range(num_days):
                current = route[-1]
                if current not in feasible_lookup:
                    valid_route = False
                    break
                
                # Get possible next places that haven't been used
                possible_next = [p for p in feasible_lookup[current] if p not in used_places]
                if not possible_next:
                    valid_route = False
                    break
                
                next_place = random.choice(possible_next)
                route.append(next_place)
                used_places.add(next_place)
            
            if not valid_route:
                continue
            
            # Convert route to waypoints
            candidate = [next(p for p in places if p['properties']['name'] == name) for name in route]
            
            # Generate legs and check distances
            legs = []
            full_route_coords = []
            valid = True
            scenic_used = [False]*num_days
            scenic_points_used = [None]*num_days
            
            for i in range(num_days):
                print(f"[LOG]  Day {i+1}: Generating leg from {candidate[i]['properties']['name']} to {candidate[i+1]['properties']['name']}")
                wp = [(candidate[i]['geometry']['coordinates'][1], candidate[i]['geometry']['coordinates'][0]),
                      (candidate[i+1]['geometry']['coordinates'][1], candidate[i+1]['geometry']['coordinates'][0])]
                wp_str = '|'.join([f"{lat},{lon}" for lat, lon in wp])
                
                # Get route with caching
                data = get_route(wp_str)
                if not data['features']:
                    print(f"[LOG]   No features returned for leg {i+1}")
                    valid = False
                    break
                
                leg = data['features'][0]['properties']
                dist_km = leg['distance']/1000
                coords = data['features'][0]['geometry']['coordinates']
                
                if data['features'][0]['geometry']['type'] == 'LineString':
                    leg_coords = [(lat, lon) for lon, lat in coords]
                else:
                    leg_coords = []
                    for seg in coords:
                        leg_coords.extend([(lat, lon) for lon, lat in seg])
                
                # Add scenic detour if needed
                if dist_km < 10:
                    mid = ((wp[0][0]+wp[1][0])/2, (wp[0][1]+wp[1][1])/2)
                    scenic_nearby = [s for s in scenic_info if geodesic(mid, s['coords']).km < 5]
                    
                    if scenic_nearby:
                        via = scenic_nearby[0]['coords']
                        wp_via = [wp[0], via, wp[1]]
                        wp_via_str = '|'.join([f"{lat},{lon}" for lat, lon in wp_via])
                        
                        data_via = get_route(wp_via_str)
                        if data_via['features']:
                            leg_via = data_via['features'][0]['properties']
                            dist_km_via = leg_via['distance']/1000
                            
                            if 10 <= dist_km_via <= 15:
                                dist_km = dist_km_via
                                leg = leg_via
                                coords = data_via['features'][0]['geometry']['coordinates']
                                if data_via['features'][0]['geometry']['type'] == 'LineString':
                                    leg_coords = [(lat, lon) for lon, lat in coords]
                                else:
                                    leg_coords = []
                                    for seg in coords:
                                        leg_coords.extend([(lat, lon) for lon, lat in seg])
                                scenic_used[i] = True
                                scenic_points_used[i] = scenic_nearby[0]
                
                if not (10 <= dist_km <= 15):
                    print(f"[LOG]   Leg {i+1} distance {dist_km} km out of bounds (10-15 km)")
                    valid = False
                    break
                
                if i > 0:
                    overlap = len(set(leg_coords) & set(full_route_coords)) / max(1, len(leg_coords))
                    if overlap > 0.2:
                        print(f"[LOG]   Leg {i+1} has too much overlap with previous legs: {overlap*100:.1f}%")
                        valid = False
                        break
                
                full_route_coords.extend(leg_coords)
                legs.append({
                    'distance': dist_km,
                    'coords': leg_coords,
                    'scenic': scenic_used[i]
                })
            
            if valid:
                score = sum((leg['distance']-12.5)**2 for leg in legs)
                if score < best_score:
                    print(f"[LOG]  New best itinerary found with score {score}")
                    best_score = score
                    best_itinerary = candidate
                    best_result = legs
                    best_scenic_points = scenic_points_used
        
        if not best_itinerary:
            print("[LOG] No valid itinerary found. Try increasing num_tries or relaxing constraints.")
            return {
                'error': 'No valid itinerary found. Try increasing num_tries or relaxing constraints.'
            }
        
        # Prepare route data
        print("[LOG] Preparing route data and generating map image")
        route_data = {
            'legs': best_result,
            'waypoints': best_itinerary,
            'scenic_points': best_scenic_points
        }
        
        # Generate map
        map_image = generate_route_map(route_data, best_itinerary, best_scenic_points)
        print("[LOG] Map image generated")
        
        # Prepare response
        response = {
            'days': [],
            'map_image': map_image
        }
        
        for i in range(num_days):
            start = best_itinerary[i]['properties']['name']
            end = best_itinerary[i+1]['properties']['name']
            dist_km = best_result[i]['distance']
            scenic = best_result[i]['scenic']
            
            day_info = {
                'day': i + 1,
                'start': start,
                'end': end,
                'distance': round(dist_km, 1)
            }
            
            if scenic and best_scenic_points[i]:
                day_info['scenic_detour'] = {
                    'name': best_scenic_points[i]['name'],
                    'type': best_scenic_points[i]['type']
                }
            
            response['days'].append(day_info)
        print(f"[LOG] Returning response with {len(response['days'])} days")
        return response
        
    except Exception as e:
        print(f"[LOG] Exception in generate_hiking_route: {e}")
        return {
            'error': str(e)
        }

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