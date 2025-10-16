import json
from geopy.distance import geodesic

def analyze_scenic_coverage():
    """Analyze how well scenic points cover the Cornwall waypoints."""
    print("=== Cornwall Scenic Midpoint Coverage Analysis ===")
    
    # Load waypoints
    with open('cornwall_waypoints.json', 'r') as f:
        waypoints = json.load(f)
    
    # Load scenic points
    with open('cache/cornwall_scenic_points.json', 'r') as f:
        scenic_points = json.load(f)
    
    print(f"Waypoints: {len(waypoints)}")
    print(f"Scenic points: {len(scenic_points)}")
    
    # Create waypoint coordinates
    waypoint_coords = {}
    for wp in waypoints:
        name = wp['properties']['name']
        coords = wp['geometry']['coordinates']
        waypoint_coords[name] = (coords[1], coords[0])  # lat, lon
    
    # Create scenic point coordinates
    scenic_coords = {}
    for sp in scenic_points:
        name = sp['name']
        coords = sp['coords']
        scenic_coords[name] = (coords[1], coords[0])  # lat, lon (coords is [lon, lat])
    
    # Analyze coverage for each waypoint pair
    print(f"\n=== Scenic Midpoint Coverage for Waypoint Pairs ===")
    
    covered_pairs = 0
    total_pairs = 0
    coverage_stats = []
    
    for wp1_name, wp1_coords in waypoint_coords.items():
        for wp2_name, wp2_coords in waypoint_coords.items():
            if wp1_name != wp2_name:
                total_pairs += 1
                
                # Calculate midpoint between waypoints
                mid_lat = (wp1_coords[0] + wp2_coords[0]) / 2
                mid_lon = (wp1_coords[1] + wp2_coords[1]) / 2
                
                # Find closest scenic point within 10km (same as Lake District)
                closest_distance = float('inf')
                closest_scenic = None
                
                for scenic_name, scenic_coord in scenic_coords.items():
                    dist = geodesic((mid_lat, mid_lon), scenic_coord).kilometers
                    if dist < 10 and dist < closest_distance:
                        closest_distance = dist
                        closest_scenic = scenic_name
                
                if closest_scenic:
                    covered_pairs += 1
                    coverage_stats.append({
                        'from': wp1_name,
                        'to': wp2_name,
                        'scenic': closest_scenic,
                        'distance': closest_distance
                    })
    
    coverage_percentage = (covered_pairs / total_pairs) * 100 if total_pairs > 0 else 0
    
    print(f"Total waypoint pairs: {total_pairs}")
    print(f"Pairs with scenic midpoints within 10km: {covered_pairs}")
    print(f"Coverage percentage: {coverage_percentage:.1f}%")
    
    # Show some examples
    print(f"\n=== Example Scenic Midpoints ===")
    for i, stat in enumerate(coverage_stats[:10]):
        print(f"{i+1}. {stat['from']} → {stat['to']}")
        print(f"   Scenic: {stat['scenic']} ({stat['distance']:.1f}km from midpoint)")
    
    if len(coverage_stats) > 10:
        print(f"   ... and {len(coverage_stats) - 10} more")
    
    # Analyze scenic point distribution
    print(f"\n=== Scenic Point Distribution ===")
    
    # Count scenic points by type
    type_counts = {}
    for sp in scenic_points:
        point_type = sp['type']
        type_counts[point_type] = type_counts.get(point_type, 0) + 1
    
    for point_type, count in type_counts.items():
        print(f"{point_type}: {count}")
    
    # Find scenic points that are most useful (appear in multiple pairs)
    scenic_usage = {}
    for stat in coverage_stats:
        scenic_name = stat['scenic']
        scenic_usage[scenic_name] = scenic_usage.get(scenic_name, 0) + 1
    
    most_used = sorted(scenic_usage.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== Most Useful Scenic Points ===")
    for scenic_name, usage_count in most_used[:10]:
        print(f"{scenic_name}: used in {usage_count} waypoint pairs")
    
    return {
        'total_pairs': total_pairs,
        'covered_pairs': covered_pairs,
        'coverage_percentage': coverage_percentage,
        'scenic_types': type_counts,
        'most_used_scenic': most_used[:5]
    }

def compare_with_lake_district():
    """Compare Cornwall scenic coverage with Lake District."""
    print(f"\n=== Comparison with Lake District ===")
    
    try:
        # Load Lake District scenic points
        with open('cache/scenic_points.json', 'r') as f:
            lake_scenic = json.load(f)
        
        # Load Lake District waypoints
        with open('filtered_waypoints.json', 'r') as f:
            lake_waypoints = json.load(f)
        
        print(f"Lake District waypoints: {len(lake_waypoints)}")
        print(f"Lake District scenic points: {len(lake_scenic)}")
        print(f"Cornwall waypoints: 29")
        print(f"Cornwall scenic points: 100")
        
        # Calculate Lake District coverage (simplified)
        lake_pairs = len(lake_waypoints) * (len(lake_waypoints) - 1)
        print(f"Lake District potential pairs: {lake_pairs}")
        print(f"Cornwall potential pairs: 29 * 28 = 812")
        
    except FileNotFoundError:
        print("Lake District data not available for comparison")

def main():
    print("Analyzing Cornwall Scenic Midpoint Coverage")
    print("=" * 50)
    
    stats = analyze_scenic_coverage()
    compare_with_lake_district()
    
    print(f"\n=== Summary ===")
    print(f"Cornwall has {stats['coverage_percentage']:.1f}% scenic midpoint coverage")
    print(f"This means {stats['covered_pairs']} out of {stats['total_pairs']} waypoint pairs have scenic midpoints")
    
    if stats['coverage_percentage'] > 50:
        print("✅ Good scenic coverage for route planning")
    elif stats['coverage_percentage'] > 25:
        print("⚠️  Moderate scenic coverage - some routes may not have scenic midpoints")
    else:
        print("❌ Low scenic coverage - many routes will lack scenic midpoints")

if __name__ == "__main__":
    main()
