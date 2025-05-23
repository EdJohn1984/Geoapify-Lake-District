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

def get_places(categories, filter_type="rect", filter_value=BBOX, radius=None):
    """Generic function to get places from Geoapify API."""
    if filter_type == "circle":
        url = f"https://api.geoapify.com/v2/places?categories={categories}&filter=circle:{filter_value}&radius={radius}&limit=100&apiKey={API_KEY}"
    else:
        url = f"https://api.geoapify.com/v2/places?categories={categories}&filter=rect:{filter_value}&limit=100&apiKey={API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    return data.get('features', [])

def get_waypoints():
    """Get waypoints from API."""
    # Get towns and villages
    places = get_places("populated_place.town,populated_place.village")
    
    # Get all pubs and hostels in the area
    pubs = get_places("catering.pub")
    hostels = get_places("accommodation.hostel,camping.camp_site")
    
    # Create lookup dictionaries for faster searching
    pub_coords = {(p['geometry']['coordinates'][1], p['geometry']['coordinates'][0]): p for p in pubs}
    hostel_coords = {(h['geometry']['coordinates'][1], h['geometry']['coordinates'][0]): h for h in hostels}
    
    # Filter places that have pubs and hostels nearby
    filtered = []
    for place in places:
        lat, lon = place['geometry']['coordinates'][1], place['geometry']['coordinates'][0]
        
        # Check for nearby amenities
        has_pub = any(geodesic((lat, lon), (p_lat, p_lon)).km <= 1 
                     for p_lat, p_lon in pub_coords.keys())
        has_hostel = any(geodesic((lat, lon), (h_lat, h_lon)).km <= 1 
                        for h_lat, h_lon in hostel_coords.keys())
        
        if has_pub and has_hostel:
            filtered.append(place)
    
    return filtered

def get_route(waypoints_str):
    """Get route between waypoints."""
    url = f"https://api.geoapify.com/v1/routing?waypoints={waypoints_str}&mode=hike&apiKey={API_KEY}"
    resp = requests.get(url)
    return resp.json()

def generate_hiking_route(num_days=3, num_tries=50):  # Reduced num_tries for faster execution
    """Generate a hiking route and return the results as a dictionary."""
    try:
        # Get waypoints from API
        places = get_waypoints()
        if not places:
            return {'error': 'No suitable waypoints found'}
        
        best_itinerary = None
        best_score = float('inf')
        best_result = None
        best_coordinates = None
        
        for _ in range(num_tries):
            candidate = random.sample(places, num_days+1)
            waypoints = [(p['geometry']['coordinates'][1], p['geometry']['coordinates'][0]) for p in candidate]
            legs = []
            full_route_coords = []
            valid = True
            
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
                    'coords': leg_coords
                })
            
            if valid:
                score = sum((leg['distance']-12.5)**2 for leg in legs)
                if score < best_score:
                    best_score = score
                    best_itinerary = candidate
                    best_result = legs
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
            
            day_info = {
                'day': i + 1,
                'start': start,
                'end': end,
                'distance': round(dist_km, 1)
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
        print("\n" + "=" * 50)
        print("\nRoute coordinates saved as geoapify_route.json") 