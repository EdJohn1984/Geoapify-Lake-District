import json
from geopy.distance import geodesic

# Load waypoints
with open('filtered_waypoints.json', 'r') as f:
    waypoints = json.load(f)

# Create a dictionary of coordinates
coords = {}
for wp in waypoints:
    name = wp['properties']['name']
    coords[name] = (wp['geometry']['coordinates'][1], wp['geometry']['coordinates'][0])

# Calculate distances between all pairs
distances = {}
feasible_pairs = []
for wp1 in coords:
    for wp2 in coords:
        if wp1 != wp2:
            dist = geodesic(coords[wp1], coords[wp2]).kilometers
            distances[(wp1, wp2)] = dist
            # Check if distance is within feasible range (5-15km)
            if 5 <= dist <= 15:
                feasible_pairs.append((wp1, wp2))

# Count potential 3-day routes
feasible_routes = []
for start in coords:
    for day1 in coords:
        if start != day1 and (start, day1) in feasible_pairs:
            for day2 in coords:
                if day2 not in [start, day1] and (day1, day2) in feasible_pairs:
                    for end in coords:
                        if end not in [start, day1, day2] and (day2, end) in feasible_pairs:
                            feasible_routes.append((start, day1, day2, end))

print(f"Total number of waypoints: {len(coords)}")
print(f"Number of feasible pairs (5-15km): {len(feasible_pairs)}")
print(f"Number of potential 3-day routes: {len(feasible_routes)}")

# Print some example feasible pairs
print("\nExample feasible pairs (5-15km):")
for wp1, wp2 in feasible_pairs[:10]:
    print(f"{wp1} to {wp2}: {distances[(wp1, wp2)]:.1f}km")

# Print some example feasible routes
print("\nExample feasible 3-day routes:")
for route in feasible_routes[:5]:
    print(f"Day 1: {route[0]} to {route[1]} ({distances[(route[0], route[1])]:.1f}km)")
    print(f"Day 2: {route[1]} to {route[2]} ({distances[(route[1], route[2])]:.1f}km)")
    print(f"Day 3: {route[2]} to {route[3]} ({distances[(route[2], route[3])]:.1f}km)")
    print("---") 