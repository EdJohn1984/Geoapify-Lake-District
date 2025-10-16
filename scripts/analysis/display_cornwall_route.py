import json
from cornwall_planner import generate_cornwall_hiking_route

def display_route_info():
    """Display the generated Cornwall route in a user-friendly format."""
    print("=== Cornwall Hiking Route ===")
    print("=" * 40)
    
    # Load waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints_data = json.load(f)
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints_data}
    
    # Generate a route
    result = generate_cornwall_hiking_route(waypoint_dict, num_days=3, max_tries=50)
    
    if not result:
        print("❌ No route could be generated")
        return
    
    print(f"🗺️  ROUTE: {' → '.join(result['waypoints'])}")
    print()
    
    # Show each day
    total_distance = 0
    total_duration = 0
    
    for i, leg in enumerate(result['legs']):
        distance_km = leg['properties']['distance'] / 1000
        duration_min = leg['properties']['time'] / 60
        total_distance += distance_km
        total_duration += duration_min
        
        print(f"📍 DAY {i+1}: {result['waypoints'][i]} → {result['waypoints'][i+1]}")
        print(f"   📏 Distance: {distance_km:.1f} km")
        print(f"   ⏱️  Duration: {duration_min:.1f} minutes ({duration_min/60:.1f} hours)")
        
        # Show scenic midpoint
        if i < len(result['scenic_midpoints']):
            midpoint = result['scenic_midpoints'][i]
            if midpoint:
                print(f"   🏔️  Scenic Highlight: {midpoint['name']} ({midpoint['type']})")
            else:
                print(f"   🏔️  Scenic Highlight: None")
        print()
    
    print(f"📊 SUMMARY:")
    print(f"   Total Distance: {total_distance:.1f} km")
    print(f"   Total Duration: {total_duration:.1f} hours")
    print(f"   Average Daily: {total_distance/len(result['legs']):.1f} km")
    print()
    
    # Show waypoint details
    print(f"📍 WAYPOINT DETAILS:")
    for i, wp_name in enumerate(result['waypoints']):
        wp_data = waypoint_dict[wp_name]
        coords = wp_data['geometry']['coordinates']
        county = wp_data['properties'].get('county', 'Unknown')
        print(f"   {i+1}. {wp_name} ({county})")
        print(f"      Coordinates: {coords[1]:.4f}, {coords[0]:.4f}")
    
    print()
    print(f"🏔️  SCENIC HIGHLIGHTS:")
    scenic_count = 0
    for i, midpoint in enumerate(result['scenic_midpoints']):
        if midpoint:
            scenic_count += 1
            print(f"   Day {i+1}: {midpoint['name']} ({midpoint['type']})")
    
    if scenic_count == 0:
        print("   No scenic highlights found for this route")
    
    print()
    print(f"📁 FILES GENERATED:")
    print(f"   - cornwall_route_map.png (Visual map)")
    print(f"   - cornwall_route.geojson (Data export)")

if __name__ == "__main__":
    display_route_info()

