import json
from geopy.distance import geodesic

def analyze_waypoints(filename, region_name):
    """Analyze waypoint data for a specific region."""
    print(f"\n=== {region_name} Waypoint Analysis ===")
    
    with open(filename, 'r') as f:
        waypoints = json.load(f)
    
    print(f"Total waypoints: {len(waypoints)}")
    
    # Create a dictionary of coordinates
    coords = {}
    for wp in waypoints:
        name = wp['properties']['name']
        coords[name] = (wp['geometry']['coordinates'][1], wp['geometry']['coordinates'][0])
    
    # Calculate distances between all pairs
    distances = []
    for wp1 in coords:
        for wp2 in coords:
            if wp1 != wp2:
                dist = geodesic(coords[wp1], coords[wp2]).kilometers
                distances.append(dist)
    
    if distances:
        print(f"Distance statistics:")
        print(f"  Min distance: {min(distances):.1f} km")
        print(f"  Max distance: {max(distances):.1f} km")
        print(f"  Average distance: {sum(distances)/len(distances):.1f} km")
        
        # Count feasible pairs (10-15km range)
        feasible_pairs = [d for d in distances if 10 <= d <= 15]
        print(f"  Feasible pairs (10-15km): {len(feasible_pairs)}")
        
        # Count potential 3-day routes
        feasible_routes = 0
        for start in coords:
            for day1 in coords:
                if start != day1 and geodesic(coords[start], coords[day1]).km >= 10 and geodesic(coords[start], coords[day1]).km <= 15:
                    for day2 in coords:
                        if day2 not in [start, day1] and geodesic(coords[day1], coords[day2]).km >= 10 and geodesic(coords[day1], coords[day2]).km <= 15:
                            for end in coords:
                                if end not in [start, day1, day2] and geodesic(coords[day2], coords[end]).km >= 10 and geodesic(coords[day2], coords[end]).km <= 15:
                                    feasible_routes += 1
        
        print(f"  Potential 3-day routes: {feasible_routes}")
    
    # Show sample waypoints
    print(f"\nSample waypoints:")
    for i, wp in enumerate(waypoints[:10]):
        name = wp['properties']['name']
        county = wp['properties'].get('county', 'Unknown')
        print(f"  {i+1}. {name} ({county})")
    
    if len(waypoints) > 10:
        print(f"  ... and {len(waypoints) - 10} more")
    
    return len(waypoints), len(feasible_pairs) if distances else 0, feasible_routes

def main():
    print("Cornwall vs Lake District Waypoint Comparison")
    
    # Analyze Cornwall waypoints
    cornwall_count, cornwall_feasible, cornwall_routes = analyze_waypoints('cornwall_waypoints.json', 'Cornwall')
    
    # Analyze Lake District waypoints
    try:
        lake_count, lake_feasible, lake_routes = analyze_waypoints('filtered_waypoints.json', 'Lake District')
        
        print(f"\n=== Comparison Summary ===")
        print(f"Waypoints: Cornwall {cornwall_count} vs Lake District {lake_count}")
        print(f"Feasible pairs: Cornwall {cornwall_feasible} vs Lake District {lake_feasible}")
        print(f"Potential 3-day routes: Cornwall {cornwall_routes} vs Lake District {lake_routes}")
        
        if cornwall_count > 0 and lake_count > 0:
            print(f"\nCornwall has {cornwall_count/lake_count:.1f}x the waypoints of Lake District")
            if cornwall_feasible > 0 and lake_feasible > 0:
                print(f"Cornwall has {cornwall_feasible/lake_feasible:.1f}x the feasible pairs of Lake District")
    
    except FileNotFoundError:
        print("\nLake District waypoints not found for comparison")

if __name__ == "__main__":
    main()

