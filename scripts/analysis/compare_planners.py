import json
from cornwall_planner import generate_cornwall_hiking_route, get_cornwall_feasible_pairs, get_cornwall_scenic_points
from geoapify_planner import generate_hiking_route, get_feasible_pairs, get_scenic_points

def compare_planners():
    """Compare Lake District and Cornwall route planners."""
    print("=== Lake District vs Cornwall Route Planner Comparison ===")
    
    # Load waypoints for both regions
    with open('filtered_waypoints.json', 'r') as f:
        lake_waypoints_data = json.load(f)
    lake_waypoint_dict = {wp['properties']['name']: wp for wp in lake_waypoints_data}
    
    with open('cornwall_waypoints.json', 'r') as f:
        cornwall_waypoints_data = json.load(f)
    cornwall_waypoint_dict = {wp['properties']['name']: wp for wp in cornwall_waypoints_data}
    
    print(f"Lake District waypoints: {len(lake_waypoint_dict)}")
    print(f"Cornwall waypoints: {len(cornwall_waypoint_dict)}")
    
    # Compare feasible pairs
    print(f"\n--- Feasible Pairs Comparison ---")
    lake_pairs = get_feasible_pairs()
    cornwall_pairs = get_cornwall_feasible_pairs()
    
    print(f"Lake District feasible pairs: {len(lake_pairs)}")
    print(f"Cornwall feasible pairs: {len(cornwall_pairs)}")
    
    # Analyze distance ranges
    lake_distances = [pair['distance'] for pair in lake_pairs]
    cornwall_distances = [pair['distance'] for pair in cornwall_pairs]
    
    print(f"\nDistance ranges:")
    print(f"Lake District: {min(lake_distances):.1f} - {max(lake_distances):.1f} km (avg: {sum(lake_distances)/len(lake_distances):.1f} km)")
    print(f"Cornwall: {min(cornwall_distances):.1f} - {max(cornwall_distances):.1f} km (avg: {sum(cornwall_distances)/len(cornwall_distances):.1f} km)")
    
    # Compare scenic points
    print(f"\n--- Scenic Points Comparison ---")
    lake_scenic = get_scenic_points()
    cornwall_scenic = get_cornwall_scenic_points()
    
    print(f"Lake District scenic points: {len(lake_scenic)}")
    print(f"Cornwall scenic points: {len(cornwall_scenic)}")
    
    # Count by type
    def count_scenic_types(scenic_points):
        type_counts = {}
        for sp in scenic_points:
            point_type = sp['type']
            type_counts[point_type] = type_counts.get(point_type, 0) + 1
        return type_counts
    
    lake_types = count_scenic_types(lake_scenic)
    cornwall_types = count_scenic_types(cornwall_scenic)
    
    print(f"\nScenic point types:")
    print(f"Lake District: {lake_types}")
    print(f"Cornwall: {cornwall_types}")
    
    # Test route generation
    print(f"\n--- Route Generation Test ---")
    
    # Test Lake District
    print(f"\nTesting Lake District routes:")
    lake_success = 0
    lake_scenic_count = 0
    
    for i in range(3):
        result = generate_hiking_route(lake_waypoint_dict, num_days=3, max_tries=20)
        if result:
            lake_success += 1
            scenic_count = len([m for m in result['scenic_midpoints'] if m])
            lake_scenic_count += scenic_count
            print(f"  Route {i+1}: {' → '.join(result['waypoints'])} (scenic: {scenic_count}/3)")
    
    # Test Cornwall
    print(f"\nTesting Cornwall routes:")
    cornwall_success = 0
    cornwall_scenic_count = 0
    
    for i in range(3):
        result = generate_cornwall_hiking_route(cornwall_waypoint_dict, num_days=3, max_tries=20)
        if result:
            cornwall_success += 1
            scenic_count = len([m for m in result['scenic_midpoints'] if m])
            cornwall_scenic_count += scenic_count
            print(f"  Route {i+1}: {' → '.join(result['waypoints'])} (scenic: {scenic_count}/3)")
    
    # Summary
    print(f"\n=== Comparison Summary ===")
    print(f"Route generation success:")
    print(f"  Lake District: {lake_success}/3 ({lake_success/3*100:.1f}%)")
    print(f"  Cornwall: {cornwall_success}/3 ({cornwall_success/3*100:.1f}%)")
    
    print(f"\nScenic midpoint integration:")
    print(f"  Lake District: {lake_scenic_count/lake_success:.1f} avg per route" if lake_success > 0 else "  Lake District: N/A")
    print(f"  Cornwall: {cornwall_scenic_count/cornwall_success:.1f} avg per route" if cornwall_success > 0 else "  Cornwall: N/A")
    
    print(f"\nKey differences:")
    print(f"  • Cornwall has {len(cornwall_waypoint_dict)/len(lake_waypoint_dict):.1f}x more waypoints")
    print(f"  • Cornwall has {len(cornwall_pairs)/len(lake_pairs):.1f}x more feasible pairs")
    print(f"  • Cornwall uses wider distance range (8-18km vs 10-15km)")
    print(f"  • Both regions have similar scenic point coverage")
    
    return {
        'lake_waypoints': len(lake_waypoint_dict),
        'cornwall_waypoints': len(cornwall_waypoint_dict),
        'lake_pairs': len(lake_pairs),
        'cornwall_pairs': len(cornwall_pairs),
        'lake_scenic': len(lake_scenic),
        'cornwall_scenic': len(cornwall_scenic),
        'lake_success': lake_success,
        'cornwall_success': cornwall_success
    }

if __name__ == "__main__":
    results = compare_planners()
    
    print(f"\n=== Final Assessment ===")
    if results['cornwall_success'] >= 2:
        print("✅ Cornwall planner is ready for production")
    else:
        print("⚠️  Cornwall planner needs more testing")
    
    if results['cornwall_pairs'] > results['lake_pairs']:
        print("✅ Cornwall has better route connectivity")
    else:
        print("⚠️  Cornwall route connectivity could be improved")

