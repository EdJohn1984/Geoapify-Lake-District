import requests
import json
from geopy.distance import geodesic

API_KEY = "01c9293b314a49979b45d9e0a5570a3f"
# Cornwall bounding box: west,south,east,north
# Based on Cornwall's geographic extent
BBOX = "-5.7,49.8,-4.0,50.9"

print(f"Fetching waypoints for Cornwall with bounding box: {BBOX}")

# Fetch towns/villages/cities
print("Fetching towns, villages, and cities...")
places_url = f"https://api.geoapify.com/v2/places?categories=populated_place.town,populated_place.village,populated_place.city&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
places_response = requests.get(places_url)
places_data = places_response.json()

if 'features' not in places_data:
    print(f"Error fetching places: {places_data}")
    exit(1)

places = places_data['features']
print(f"Found {len(places)} populated places")

# Fetch pubs
print("Fetching pubs...")
pubs_url = f"https://api.geoapify.com/v2/places?categories=catering.pub&filter=rect:{BBOX}&limit=500&apiKey={API_KEY}"
pubs_response = requests.get(pubs_url)
pubs_data = pubs_response.json()

if 'features' not in pubs_data:
    print(f"Error fetching pubs: {pubs_data}")
    exit(1)

pubs = pubs_data['features']
print(f"Found {len(pubs)} pubs")

# Fetch hostels/campsites
print("Fetching hostels and campsites...")
hostels_url = f"https://api.geoapify.com/v2/places?categories=accommodation.hostel,camping.camp_site&filter=rect:{BBOX}&limit=500&apiKey={API_KEY}"
hostels_response = requests.get(hostels_url)
hostels_data = hostels_response.json()

if 'features' not in hostels_data:
    print(f"Error fetching hostels: {hostels_data}")
    exit(1)

hostels = hostels_data['features']
print(f"Found {len(hostels)} hostels and campsites")

# Precompute pub and hostel/campsite coordinates
pub_coords = [(p['geometry']['coordinates'][1], p['geometry']['coordinates'][0]) for p in pubs]
hostel_coords = [(h['geometry']['coordinates'][1], h['geometry']['coordinates'][0]) for h in hostels]

print("Filtering waypoints...")
filtered = []
for place in places:
    lat, lon = place['geometry']['coordinates'][1], place['geometry']['coordinates'][0]
    place_name = place['properties'].get('name', 'Unknown')
    
    # Check for pub within 1km
    has_pub = any(geodesic((lat, lon), pub).km <= 1 for pub in pub_coords)
    # Check for hostel/campsite within 1km
    has_hostel = any(geodesic((lat, lon), hostel).km <= 1 for hostel in hostel_coords)
    
    if has_pub and has_hostel:
        filtered.append(place)
        print(f"✓ {place_name} - has both pub and accommodation within 1km")
    else:
        print(f"✗ {place_name} - missing pub or accommodation")

# Save filtered waypoints
with open('cornwall_waypoints.json', 'w') as f:
    json.dump(filtered, f, indent=2)

print(f"\nFiltered {len(filtered)} waypoints with both pub and hostel/campsite within 1km.")
print("Saved to cornwall_waypoints.json")

# Print some statistics
if filtered:
    print(f"\nSample filtered waypoints:")
    for i, wp in enumerate(filtered[:5]):
        name = wp['properties'].get('name', 'Unknown')
        county = wp['properties'].get('county', 'Unknown')
        print(f"  {i+1}. {name} ({county})")
    
    if len(filtered) > 5:
        print(f"  ... and {len(filtered) - 5} more")
else:
    print("\nNo waypoints found matching the criteria. You may need to:")
    print("1. Adjust the bounding box")
    print("2. Relax the distance requirements")
    print("3. Check if there are sufficient pubs and accommodations in the area")

