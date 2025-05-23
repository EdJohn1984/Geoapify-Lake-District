import requests
import random
import json
from geopy.distance import geodesic
import os
from datetime import datetime, timedelta

# Get API key from environment variable or use default
API_KEY = os.getenv('GEOAPIFY_API_KEY', "01c9293b314a49979b45d9e0a5570a3f")
# Lake District bounding box: west,south,east,north
BBOX = "-3.3,54.2,-2.7,54.6"

# Cache directory setup
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_scenic_points():
    """Fetch scenic points."""
    # Fetch new data
    scenic_url = f"https://api.geoapify.com/v2/places?categories=natural.mountain.peak,tourism.attraction.viewpoint&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
    scenic_resp = requests.get(scenic_url)
    scenic_data = scenic_resp.json()
    
    if 'features' not in scenic_data:
        raise Exception("Error in Scenic API response")
    
    # Process the data
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
    
    return scenic_info

def get_route(waypoints_str):
    """Get route between waypoints."""
    url = f"https://api.geoapify.com/v1/routing?waypoints={waypoints_str}&mode=hike&apiKey={API_KEY}"
    resp = requests.get(url)
    return resp.json()

def get_waypoints():
    """Get waypoints from API instead of file."""
    url = f"https://api.geoapify.com/v2/places?categories=populated_place.town,populated_place.village,populated_place.city&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
    places = requests.get(url).json()['features']
    
    # Filter places that have pubs and hostels nearby
    filtered = []
    for place in places:
        lat, lon = place['geometry']['coordinates'][1], place['geometry']['coordinates'][0]
        
        # Check for pub within 1km
        pubs_url = f"https://api.geoapify.com/v2/places?categories=catering.pub&filter=circle:{lon},{lat},1000&apiKey={API_KEY}"
        pubs = requests.get(pubs_url).json()['features']
        
        # Check for hostel/campsite within 1km
        hostels_url = f"https://api.geoapify.com/v2/places?categories=accommodation.hostel,camping.camp_site&filter=circle:{lon},{lat},1000&apiKey={API_KEY}"
        hostels = requests.get(hostels_url).json()['features']
        
        if pubs and hostels:
            filtered.append(place)
    
    return filtered

def generate_hiking_route(num_days=3, num_tries=200, generate_map=False):
    """Generate a hiking route and return the results as a dictionary."""
    try:
        # Get waypoints from API
        places = get_waypoints()
        if not places:
            return {'error': 'No suitable waypoints found'}
        
        # Get scenic points
        scenic_info = get_scenic_points()
        
        best_itinerary = None
        best_score = float('inf')
        best_result = None
        best_scenic_points = None
        best_coordinates = None
        
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
                
                # Get route
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
                    best_coordinates = full_route_coords
        
        if not best_itinerary:
            return {
                'error': 'No valid itinerary found. Try increasing num_tries or relaxing constraints.'
            }
        
        # Prepare response
        response = {
            'days': [],
            'coordinates': best_coordinates
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
        print("\nRoute coordinates saved as geoapify_route.json") 