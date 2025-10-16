import json
from cornwall_planner import (
    generate_cornwall_hiking_route, 
    generate_cornwall_route_map,
    export_cornwall_route_to_geojson,
    get_cornwall_feasible_pairs,
    get_cornwall_scenic_points
)

def test_cornwall_route_generation():
    """Test Cornwall route generation and create visual output."""
    print("=== Cornwall Route Generation Test ===")
    
    # Load waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints_data = json.load(f)
    
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints_data}
    print(f"Loaded {len(waypoint_dict)} Cornwall waypoints")
    
    # Show some waypoint options
    print(f"\nSample waypoints available:")
    for i, name in enumerate(list(waypoint_dict.keys())[:10]):
        wp = waypoint_dict[name]
        county = wp['properties'].get('county', 'Unknown')
        print(f"  {i+1}. {name} ({county})")
    
    # Generate a route
    print(f"\n--- Generating Cornwall Route ---")
    result = generate_cornwall_hiking_route(waypoint_dict, num_days=3, max_tries=100)
    
    if not result:
        print("❌ No route could be generated")
        return None
    
    print(f"✅ Route generated successfully!")
    
    # Display route details
    print(f"\n=== Route Details ===")
    print(f"Waypoints: {' → '.join(result['waypoints'])}")
    print(f"Total legs: {len(result['legs'])}")
    print(f"Scenic midpoints: {len([m for m in result['scenic_midpoints'] if m])}")
    
    # Show each day's details
    total_distance = 0
    total_duration = 0
    
    for i, leg in enumerate(result['legs']):
        distance_km = leg['properties']['distance'] / 1000
        duration_min = leg['properties']['time'] / 60
        total_distance += distance_km
        total_duration += duration_min
        
        print(f"\nDay {i+1}: {result['waypoints'][i]} → {result['waypoints'][i+1]}")
        print(f"  📏 Distance: {distance_km:.1f} km")
        print(f"  ⏱️  Duration: {duration_min:.1f} minutes ({duration_min/60:.1f} hours)")
        
        # Show scenic midpoint if available
        if i < len(result['scenic_midpoints']):
            midpoint = result['scenic_midpoints'][i]
            if midpoint:
                print(f"  🏔️  Scenic: {midpoint['name']} ({midpoint['type']})")
            else:
                print(f"  🏔️  Scenic: No scenic midpoint found")
    
    print(f"\n📊 Route Summary:")
    print(f"  Total distance: {total_distance:.1f} km")
    print(f"  Total duration: {total_duration:.1f} minutes ({total_duration/60:.1f} hours)")
    print(f"  Average daily distance: {total_distance/len(result['legs']):.1f} km")
    print(f"  Average daily duration: {total_duration/len(result['legs']):.1f} minutes")
    
    # Generate route map
    print(f"\n--- Generating Route Map ---")
    try:
        map_image = generate_cornwall_route_map(result, waypoint_dict, result['scenic_midpoints'])
        if map_image:
            # Save map to file
            import base64
            with open('cornwall_route_map.png', 'wb') as f:
                f.write(base64.b64decode(map_image))
            print(f"✅ Route map saved as 'cornwall_route_map.png'")
        else:
            print(f"❌ Failed to generate route map")
    except Exception as e:
        print(f"❌ Error generating map: {e}")
    
    # Export to GeoJSON
    print(f"\n--- Exporting to GeoJSON ---")
    try:
        geojson_data = export_cornwall_route_to_geojson(result, waypoint_dict, result['scenic_midpoints'])
        with open('cornwall_route.geojson', 'w') as f:
            json.dump(geojson_data, f, indent=2)
        print(f"✅ Route exported to 'cornwall_route.geojson'")
        
        # Show GeoJSON summary
        print(f"GeoJSON contains:")
        print(f"  - {len([f for f in geojson_data['features'] if f['properties'].get('type') == 'waypoint'])} waypoints")
        print(f"  - {len([f for f in geojson_data['features'] if f['properties'].get('type') == 'scenic_midpoint'])} scenic midpoints")
        print(f"  - {len([f for f in geojson_data['features'] if f['properties'].get('name', '').startswith('Day')])} route legs")
        
    except Exception as e:
        print(f"❌ Error exporting GeoJSON: {e}")
    
    # Show scenic points analysis
    print(f"\n--- Scenic Points Analysis ---")
    scenic_points = get_cornwall_scenic_points()
    used_scenic = [m for m in result['scenic_midpoints'] if m]
    
    print(f"Total scenic points available: {len(scenic_points)}")
    print(f"Scenic points used in route: {len(used_scenic)}")
    
    if used_scenic:
        print(f"Scenic points in this route:")
        for i, scenic in enumerate(used_scenic):
            print(f"  Day {i+1}: {scenic['name']} ({scenic['type']})")
    
    # Show feasible pairs analysis
    print(f"\n--- Route Connectivity Analysis ---")
    feasible_pairs = get_cornwall_feasible_pairs()
    print(f"Total feasible pairs: {len(feasible_pairs)}")
    
    # Check if the generated route uses feasible pairs
    route_pairs = []
    for i in range(len(result['waypoints']) - 1):
        from_wp = result['waypoints'][i]
        to_wp = result['waypoints'][i + 1]
        route_pairs.append((from_wp, to_wp))
    
    feasible_route_pairs = 0
    for from_wp, to_wp in route_pairs:
        is_feasible = any(p['from'] == from_wp and p['to'] == to_wp for p in feasible_pairs)
        if is_feasible:
            feasible_route_pairs += 1
        print(f"  {from_wp} → {to_wp}: {'✅ Feasible' if is_feasible else '❌ Not feasible'}")
    
    print(f"Route feasibility: {feasible_route_pairs}/{len(route_pairs)} pairs are feasible")
    
    return result

def show_waypoint_details():
    """Show detailed information about Cornwall waypoints."""
    print(f"\n=== Cornwall Waypoint Details ===")
    
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints = json.load(f)
    
    print(f"Total waypoints: {len(waypoints)}")
    
    # Group by county
    counties = {}
    for wp in waypoints:
        county = wp['properties'].get('county', 'Unknown')
        if county not in counties:
            counties[county] = []
        counties[county].append(wp['properties']['name'])
    
    print(f"\nWaypoints by county:")
    for county, names in counties.items():
        print(f"  {county}: {len(names)} waypoints")
        for name in names[:5]:  # Show first 5
            print(f"    - {name}")
        if len(names) > 5:
            print(f"    ... and {len(names) - 5} more")
    
    # Show some specific waypoints with coordinates
    print(f"\nSample waypoint coordinates:")
    for i, wp in enumerate(waypoints[:5]):
        name = wp['properties']['name']
        coords = wp['geometry']['coordinates']
        county = wp['properties'].get('county', 'Unknown')
        print(f"  {i+1}. {name} ({county}): {coords[1]:.4f}, {coords[0]:.4f}")

if __name__ == "__main__":
    print("Testing Cornwall Route Generation and Mapping")
    print("=" * 50)
    
    # Show waypoint details first
    show_waypoint_details()
    
    # Generate and test route
    result = test_cornwall_route_generation()
    
    if result:
        print(f"\n🎉 Cornwall route generation test completed successfully!")
        print(f"Check the generated files:")
        print(f"  - cornwall_route_map.png (visual map)")
        print(f"  - cornwall_route.geojson (data export)")
    else:
        print(f"\n❌ Cornwall route generation test failed")

