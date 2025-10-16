import requests
import json
from datetime import datetime, timedelta
import os

API_KEY = "01c9293b314a49979b45d9e0a5570a3f"
# Cornwall bounding box: west,south,east,north
BBOX = "-5.7,49.8,-4.0,50.9"

# Cache directory setup
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def fetch_cornwall_scenic_points():
    """Fetch and cache scenic points for Cornwall."""
    cache_file = os.path.join(CACHE_DIR, "cornwall_scenic_points.json")
    
    # Check if cache is valid (less than 24 hours old)
    if os.path.exists(cache_file):
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
        if file_age < timedelta(hours=24):
            print(f"Using cached scenic points (age: {file_age})")
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    print("Fetching fresh scenic points for Cornwall...")
    
    # Fetch scenic points - mountains, peaks, viewpoints
    scenic_url = f"https://api.geoapify.com/v2/places?categories=natural.mountain.peak,tourism.attraction.viewpoint&filter=rect:{BBOX}&limit=100&apiKey={API_KEY}"
    scenic_resp = requests.get(scenic_url)
    scenic_data = scenic_resp.json()
    
    if 'features' not in scenic_data:
        print(f"Error in Scenic API response: {scenic_data}")
        return []
    
    print(f"Found {len(scenic_data['features'])} scenic points")
    
    # Process the data
    scenic_info = []
    for s in scenic_data['features']:
        name = s['properties'].get('name', 'Unnamed Point')
        categories = s['properties'].get('categories', [])
        
        # Determine scenic type
        if 'natural.mountain.peak' in categories:
            scenic_type = 'Peak'
        elif 'tourism.attraction.viewpoint' in categories:
            scenic_type = 'Viewpoint'
        else:
            scenic_type = 'Scenic Point'
        
        lon, lat = s['geometry']['coordinates'][0], s['geometry']['coordinates'][1]
        scenic_info.append({
            'name': name,
            'type': scenic_type,
            'coords': [lon, lat]
        })
    
    # Cache the results
    with open(cache_file, 'w') as f:
        json.dump(scenic_info, f)
    
    print(f"Processed and cached {len(scenic_info)} scenic points")
    return scenic_info

def analyze_scenic_points(scenic_points):
    """Analyze the scenic points data."""
    print(f"\n=== Cornwall Scenic Points Analysis ===")
    print(f"Total scenic points: {len(scenic_points)}")
    
    # Count by type
    type_counts = {}
    for point in scenic_points:
        point_type = point['type']
        type_counts[point_type] = type_counts.get(point_type, 0) + 1
    
    print(f"By type:")
    for point_type, count in type_counts.items():
        print(f"  {point_type}: {count}")
    
    # Show sample points
    print(f"\nSample scenic points:")
    for i, point in enumerate(scenic_points[:10]):
        print(f"  {i+1}. {point['name']} ({point['type']})")
    
    if len(scenic_points) > 10:
        print(f"  ... and {len(scenic_points) - 10} more")
    
    return scenic_points

def main():
    print("Fetching Cornwall Scenic Points")
    print(f"Bounding box: {BBOX}")
    
    scenic_points = fetch_cornwall_scenic_points()
    analyze_scenic_points(scenic_points)
    
    print(f"\nScenic points saved to cache/cornwall_scenic_points.json")

if __name__ == "__main__":
    main()

