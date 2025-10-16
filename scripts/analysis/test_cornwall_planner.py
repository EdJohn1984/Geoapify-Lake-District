import json
from cornwall_planner import generate_cornwall_hiking_route, get_cornwall_feasible_pairs, get_cornwall_scenic_points

def test_cornwall_planner():
    """Comprehensive test of the Cornwall route planner."""
    print("=== Cornwall Route Planner Test ===")
    
    # Load waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints_data = json.load(f)
    
    waypoint_dict = {wp['properties']['name']: wp for wp in waypoints_data}
    print(f"Loaded {len(waypoint_dict)} waypoints")
    
    # Test feasible pairs
    print("\n--- Testing Feasible Pairs ---")
    feasible_pairs = get_cornwall_feasible_pairs()
    print(f"Found {len(feasible_pairs)} feasible pairs")
    
    # Show some examples
    print("Sample feasible pairs:")
    for i, pair in enumerate(feasible_pairs[:5]):
        print(f"  {i+1}. {pair['from']} → {pair['to']} ({pair['distance']:.1f} km)")
    
    # Test scenic points
    print("\n--- Testing Scenic Points ---")
    scenic_points = get_cornwall_scenic_points()
    print(f"Found {len(scenic_points)} scenic points")
    
    # Count by type
    type_counts = {}
    for sp in scenic_points:
        point_type = sp['type']
        type_counts[point_type] = type_counts.get(point_type, 0) + 1
    
    print("Scenic points by type:")
    for point_type, count in type_counts.items():
        print(f"  {point_type}: {count}")
    
    # Test route generation
    print("\n--- Testing Route Generation ---")
    
    successful_routes = 0
    routes_with_scenic = 0
    total_scenic_midpoints = 0
    
    # Test multiple route generations
    for attempt in range(5):
        print(f"\nRoute attempt {attempt + 1}:")
        result = generate_cornwall_hiking_route(waypoint_dict, num_days=3, max_tries=50)
        
        if result:
            successful_routes += 1
            scenic_count = len([m for m in result['scenic_midpoints'] if m])
            total_scenic_midpoints += scenic_count
            
            if scenic_count > 0:
                routes_with_scenic += 1
            
            print(f"  ✅ Route: {' → '.join(result['waypoints'])}")
            print(f"  📍 Scenic midpoints: {scenic_count}/3")
            print(f"  📏 Total distance: {sum(leg['properties']['distance'] for leg in result['legs'])/1000:.1f} km")
            print(f"  ⏱️  Total duration: {sum(leg['properties']['time'] for leg in result['legs'])/60:.1f} minutes")
            
            # Show scenic midpoints
            for i, midpoint in enumerate(result['scenic_midpoints']):
                if midpoint:
                    print(f"    Day {i+1}: {midpoint['name']} ({midpoint['type']})")
        else:
            print(f"  ❌ No route found")
    
    # Summary statistics
    print(f"\n=== Test Results Summary ===")
    print(f"Successful routes: {successful_routes}/5 ({successful_routes/5*100:.1f}%)")
    print(f"Routes with scenic midpoints: {routes_with_scenic}/{successful_routes} ({routes_with_scenic/successful_routes*100:.1f}%)" if successful_routes > 0 else "N/A")
    print(f"Average scenic midpoints per route: {total_scenic_midpoints/successful_routes:.1f}" if successful_routes > 0 else "N/A")
    
    # Test specific waypoint combinations
    print(f"\n--- Testing Specific Waypoint Combinations ---")
    
    # Test some known good combinations
    test_combinations = [
        ["St Ives", "Newquay", "Falmouth"],
        ["Padstow", "New Polzeath", "St. Columb Minor"],
        ["Polruan", "Falmouth", "Coverack"]
    ]
    
    for i, combo in enumerate(test_combinations):
        print(f"\nTesting combination {i+1}: {' → '.join(combo)}")
        
        # Check if all waypoints exist
        missing = [wp for wp in combo if wp not in waypoint_dict]
        if missing:
            print(f"  ❌ Missing waypoints: {missing}")
            continue
        
        # Check if combinations are feasible
        feasible = True
        for j in range(len(combo) - 1):
            from_wp = combo[j]
            to_wp = combo[j + 1]
            pair_exists = any(p['from'] == from_wp and p['to'] == to_wp for p in feasible_pairs)
            if not pair_exists:
                print(f"  ❌ Not feasible: {from_wp} → {to_wp}")
                feasible = False
        
        if feasible:
            print(f"  ✅ All pairs are feasible")
        else:
            print(f"  ⚠️  Some pairs are not feasible")
    
    return {
        'successful_routes': successful_routes,
        'routes_with_scenic': routes_with_scenic,
        'total_scenic_midpoints': total_scenic_midpoints,
        'feasible_pairs': len(feasible_pairs),
        'scenic_points': len(scenic_points)
    }

if __name__ == "__main__":
    results = test_cornwall_planner()
    
    print(f"\n=== Overall Assessment ===")
    if results['successful_routes'] >= 4:
        print("✅ Route generation is working well")
    elif results['successful_routes'] >= 2:
        print("⚠️  Route generation is working but could be improved")
    else:
        print("❌ Route generation needs improvement")
    
    if results['routes_with_scenic'] / results['successful_routes'] >= 0.6:
        print("✅ Scenic midpoint integration is working well")
    elif results['routes_with_scenic'] / results['successful_routes'] >= 0.3:
        print("⚠️  Scenic midpoint integration is moderate")
    else:
        print("❌ Scenic midpoint integration needs improvement")

