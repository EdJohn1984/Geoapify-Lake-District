from geoapify_planner import generate_hiking_route, generate_route_map, get_scenic_points
import json
import matplotlib.pyplot as plt
from PIL import Image
import io
import base64

def test_route_generation():
    # Load waypoints
    with open('filtered_waypoints.json', 'r') as f:
        waypoints = json.load(f)
    
    # Print first 10 scenic points for debugging
    print("\nFirst 10 scenic points:")
    scenic_points = get_scenic_points()
    for s in scenic_points[:10]:
        print(f"{s['name']} - {s['type']} - lat: {s['coords'][0]}, lon: {s['coords'][1]}")
    print(f"Total scenic points: {len(scenic_points)}")
    
    # Print min/max latitude and longitude of all scenic points
    lats = [s['coords'][0] for s in scenic_points]
    lons = [s['coords'][1] for s in scenic_points]
    print(f"Scenic points latitude range: {min(lats)} to {max(lats)}")
    print(f"Scenic points longitude range: {min(lons)} to {max(lons)}")
    
    # Create waypoint dictionary
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
    
    # Generate route
    print("\nGenerating route with scenic midpoints...")
    result = generate_hiking_route(waypoint_dict, num_days=3)
    
    if not result:
        print("Failed to generate route")
        return
    
    # Print route details
    print('\nRoute Details:')
    print('=' * 50)
    
    for i, (wp, leg) in enumerate(zip(result['waypoints'], result['legs'])):
        print(f'\nDay {i+1}:')
        print(f'From: {wp}')
        print(f'To: {result["waypoints"][i+1]}')
        print(f'Distance: {leg["properties"]["distance"]/1000:.1f}km')
        if i < len(result["scenic_midpoints"]):
            print(f'Scenic Midpoint: {result["scenic_midpoints"][i]["name"]} ({result["scenic_midpoints"][i]["type"]})')
        # Print route coordinates for debugging
        print(f'Route coordinates: {leg["coords"][:3]} ... {leg["coords"][-3:]} (total {len(leg["coords"])})')
    
    # Print all scenic midpoints
    print("\nAll scenic midpoints:")
    for mid in result['scenic_midpoints']:
        print(mid)
    
    # Generate and save route map
    print("\nGenerating route map...")
    map_image = generate_route_map(result, waypoints, result['scenic_midpoints'])
    
    # Convert base64 to image and save
    image_data = base64.b64decode(map_image)
    image = Image.open(io.BytesIO(image_data))
    image.save('test_route_map.png')
    print("\nRoute map saved as 'test_route_map.png'")

if __name__ == "__main__":
    test_route_generation() 