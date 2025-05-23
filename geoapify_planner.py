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
    """Generate a hiking route and return the results as a dictionary."""
    try:
        # Load waypoints
        with open('filtered_waypoints.json', 'r') as f:
            places = json.load(f)
        
        # Get scenic points
        scenic_info = get_scenic_points()
        
        best_itinerary = None
        best_score = float('inf')
        best_result = None
        best_scenic_points = None
        
        for _ in range(num_tries):
            candidate = random.sample(places, num_days+1)
            waypoints = [(p['geometry']['coordinates'][1], p['geometry']['coordinates'][0]) for p in candidate]
            legs = []
            full_route_coords = []
            valid = True
            scenic_used = [False]*num_days
            scenic_points_used = [None]*num_days
            
            for i in range(num_days):
                wp = [waypoints[i], waypoints[i+1]]
                wp_str = '|'.join([f"{lat},{lon}" for lat, lon in wp])
                
                # Get route with caching
                data = get_route(wp_str)
                if not data['features']:
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
                    valid = False
                    break
                
                if i > 0:
                    overlap = len(set(leg_coords) & set(full_route_coords)) / max(1, len(leg_coords))
                    if overlap > 0.2:
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
                    best_score = score
                    best_itinerary = candidate
                    best_result = legs
                    best_scenic_points = scenic_points_used
        
        if not best_itinerary:
            return {
                'error': 'No valid itinerary found. Try increasing num_tries or relaxing constraints.'
            }
        
        # Prepare route data
        route_data = {
            'legs': best_result,
            'waypoints': best_itinerary,
            'scenic_points': best_scenic_points
        }
        
        # Generate map
        map_image = generate_route_map(route_data, best_itinerary, best_scenic_points)
        
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
        
        return response
        
    except Exception as e:
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