import requests
import json
from geopy.distance import geodesic

API_KEY = "01c9293b314a49979b45d9e0a5570a3f"
BBOX = "-3.3,54.2,-2.7,54.6"

# Fetch towns/villages/cities
places_url = f"https://api.geoapify.com/v2/places?categories=populated_place.town,populated_place.village,populated_place.city&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
places = requests.get(places_url).json()['features']

# Fetch pubs
pubs_url = f"https://api.geoapify.com/v2/places?categories=catering.pub&filter=rect:{BBOX}&limit=500&apiKey={API_KEY}"
pubs = requests.get(pubs_url).json()['features']

# Fetch hostels/campsites
hostels_url = f"https://api.geoapify.com/v2/places?categories=accommodation.hostel,camping.camp_site&filter=rect:{BBOX}&limit=500&apiKey={API_KEY}"
hostels = requests.get(hostels_url).json()['features']

# Precompute pub and hostel/campsite coordinates
pub_coords = [(p['geometry']['coordinates'][1], p['geometry']['coordinates'][0]) for p in pubs]
hostel_coords = [(h['geometry']['coordinates'][1], h['geometry']['coordinates'][0]) for h in hostels]

filtered = []
for place in places:
    lat, lon = place['geometry']['coordinates'][1], place['geometry']['coordinates'][0]
    # Check for pub within 1km
    has_pub = any(geodesic((lat, lon), pub).km <= 1 for pub in pub_coords)
    # Check for hostel/campsite within 1km
    has_hostel = any(geodesic((lat, lon), hostel).km <= 1 for hostel in hostel_coords)
    if has_pub and has_hostel:
        filtered.append(place)

with open('filtered_waypoints.json', 'w') as f:
    json.dump(filtered, f)

print(f"Filtered {len(filtered)} waypoints with both pub and hostel/campsite within 1km. Saved to filtered_waypoints.json.") 