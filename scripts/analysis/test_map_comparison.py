#!/usr/bin/env python3
"""
Test script to demonstrate the difference between old and new map generation
with proper OpenStreetMap basemap.
"""

from geoapify_planner import generate_hiking_route, generate_route_map
import json
import base64
from PIL import Image
import io

def test_map_generation():
    """Test the updated map generation with OpenStreetMap basemap."""
    
    print("Testing Updated Map Generation with OpenStreetMap Basemap")
    print("=" * 60)
    
    # Load waypoints
    with open('filtered_waypoints.json', 'r') as f:
        waypoints = json.load(f)
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints}
    
    # Generate a route
    print("Generating hiking route...")
    result = generate_hiking_route(waypoint_dict, num_days=3, max_tries=20)
    
    if not result:
        print("Failed to generate route")
        return
    
    print(f"Route generated: {' -> '.join(result['waypoints'])}")
    print(f"Route score: {result.get('score', 'N/A')}")
    
    # Generate map with OpenStreetMap basemap
    print("\nGenerating map with OpenStreetMap basemap...")
    map_image = generate_route_map(result, waypoints, result['scenic_midpoints'])
    
    # Save the map
    image_data = base64.b64decode(map_image)
    image = Image.open(io.BytesIO(image_data))
    image.save('openstreetmap_route.png')
    
    print("✅ Map saved as 'openstreetmap_route.png'")
    print("\nThe map now includes:")
    print("- OpenStreetMap basemap with roads, rivers, buildings")
    print("- Route waypoints with day markers")
    print("- Scenic midpoints (peaks and viewpoints)")
    print("- Route path connecting all points")
    print("- Proper geographic context for navigation")
    
    # Print route details
    print(f"\nRoute Details:")
    print("-" * 40)
    for i, leg in enumerate(result['legs']):
        print(f"Day {i+1}: {result['waypoints'][i]} → {result['waypoints'][i+1]}")
        print(f"  Distance: {leg['properties']['distance']/1000:.1f}km")
        print(f"  Duration: {leg['properties']['time']/60:.0f} minutes")
        if i < len(result['scenic_midpoints']):
            midpoint = result['scenic_midpoints'][i]
            print(f"  Scenic Point: {midpoint['name']} ({midpoint['type']})")
        print()

if __name__ == "__main__":
    test_map_generation()
