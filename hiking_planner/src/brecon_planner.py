import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from typing import List, Dict, Tuple
from shapely.geometry import Point, MultiPoint
import json
import sys
import traceback
import random
from base_planner import BasePlanner

class BreconBeaconsPlanner(BasePlanner):
    def __init__(self):
        super().__init__()
        # Define the bounding box for Brecon Beacons National Park
        self.bbox = (51.75, 52.05, -3.9, -3.3)  # (south, north, west, east)
        self.graph = None
        self.scenic_points = None
        self.towns = None
        self.accommodations = None
        
    def get_region_bbox(self) -> Tuple[float, float, float, float]:
        """Return the bounding box for Brecon Beacons National Park."""
        return (51.75, 52.05, -3.9, -3.3)  # (south, north, west, east)
        
    def get_region_name(self) -> str:
        """Return the name of the region."""
        return "Brecon Beacons"
        
    def get_notable_locations(self) -> Dict[str, Tuple[float, float]]:
        """Return a dictionary of notable locations in the region."""
        return {
            'Brecon': (51.9479, -3.3909),
            'Abergavenny': (51.8247, -3.0167),
            'Hay-on-Wye': (52.0747, -3.1278),
            'Talgarth': (51.9947, -3.2328),
            'Crickhowell': (51.8597, -3.1378),
            'Llangorse': (51.9297, -3.2628),
            'Llanfrynach': (51.9297, -3.3628),
            'Llanhamlach': (51.9297, -3.4628),
            'Llangynidr': (51.8597, -3.2278),
            'Llanbedr': (51.9297, -3.1628)
        }
        
    def fetch_osm_data(self):
        """Fetch OpenStreetMap data for the Brecon Beacons region."""
        try:
            print("Starting to fetch OSM data...", file=sys.stderr)
            # Include hiking paths and tracks
            self.graph = ox.graph_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                network_type='walk',
                custom_filter='["highway"~"path|track|footway|bridleway|steps"]'
            )
            # Project the graph to UTM
            self.graph = ox.project_graph(self.graph)
            print(f"Successfully fetched OSM data. Graph has {len(self.graph.nodes)} nodes.", file=sys.stderr)
        except Exception as e:
            print(f"Error fetching OSM data: {str(e)}", file=sys.stderr)
            raise

    def fetch_towns(self):
        """Fetch towns and villages in the region."""
        try:
            print("Fetching towns and villages...", file=sys.stderr)
            towns = ox.features_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                tags={'place': ['town', 'village', 'hamlet']}
            )
            
            # Project to UTM before calculating centroids
            towns = towns.to_crs(epsg=32630)  # UTM zone 30N for Brecon Beacons
            towns['geometry'] = towns.geometry.centroid
            # Project back to WGS84 for compatibility with other functions
            towns = towns.to_crs(epsg=4326)
            self.towns = towns
            print(f"Found {len(towns)} towns/villages", file=sys.stderr)
            return towns
        except Exception as e:
            print(f"Error fetching towns: {str(e)}", file=sys.stderr)
            raise

    def fetch_pubs(self):
        """Fetch all pubs in the region."""
        try:
            print("Fetching pubs...", file=sys.stderr)
            pubs = ox.features_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                tags={'amenity': 'pub'}
            )
            # Project to UTM before calculating centroids
            pubs = pubs.to_crs(epsg=32630)
            pubs['geometry'] = pubs.geometry.centroid
            # Project back to WGS84
            pubs = pubs.to_crs(epsg=4326)
            print(f"Found {len(pubs)} pubs", file=sys.stderr)
            return pubs
        except Exception as e:
            print(f"Error fetching pubs: {str(e)}", file=sys.stderr)
            raise

    def fetch_campsites(self):
        """Fetch all campsites in the region."""
        try:
            print("Fetching campsites...", file=sys.stderr)
            campsites = ox.features_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                tags={'tourism': 'camp_site'}
            )
            # Project to UTM before calculating centroids
            campsites = campsites.to_crs(epsg=32630)
            campsites['geometry'] = campsites.geometry.centroid
            # Project back to WGS84
            campsites = campsites.to_crs(epsg=4326)
            print(f"Found {len(campsites)} campsites", file=sys.stderr)
            return campsites
        except Exception as e:
            print(f"Error fetching campsites: {str(e)}", file=sys.stderr)
            raise

    def fetch_hostels(self):
        """Fetch all hostels in the region."""
        try:
            print("Fetching hostels...", file=sys.stderr)
            hostels = ox.features_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                tags={'tourism': 'hostel'}
            )
            # Project to UTM before calculating centroids
            hostels = hostels.to_crs(epsg=32630)
            hostels['geometry'] = hostels.geometry.centroid
            # Project back to WGS84
            hostels = hostels.to_crs(epsg=4326)
            print(f"Found {len(hostels)} hostels", file=sys.stderr)
            return hostels
        except Exception as e:
            print(f"Error fetching hostels: {str(e)}", file=sys.stderr)
            raise

    def fetch_accommodations(self):
        """Fetch hostels and campsites in the region."""
        try:
            print("Fetching hostels and campsites...", file=sys.stderr)
            accommodations = ox.features_from_bbox(
                self.bbox[1], self.bbox[0], self.bbox[2], self.bbox[3],
                tags={'tourism': ['hostel', 'camp_site']}
            )
            # Convert accommodation geometries to centroids
            accommodations['geometry'] = accommodations.geometry.centroid
            self.accommodations = accommodations
            print(f"Found {len(accommodations)} hostels/campsites", file=sys.stderr)
            return accommodations
        except Exception as e:
            print(f"Error fetching accommodations: {str(e)}", file=sys.stderr)
            raise

    def identify_scenic_locations(self) -> List[Dict]:
        """Identify scenic locations in the Brecon Beacons."""
        try:
            print("Identifying scenic locations...", file=sys.stderr)
            bbox = self.get_region_bbox()
            
            # Get points of interest that might be scenic
            tags = {
                'natural': ['peak', 'cliff', 'waterfall'],
                'tourism': ['viewpoint'],
                'historic': ['ruins', 'monument']
            }
            
            scenic_points = []
            for category, values in tags.items():
                for value in values:
                    places = ox.features_from_bbox(
                        bbox[1], bbox[0], bbox[2], bbox[3],
                        tags={category: value}
                    )
                    if not places.empty:
                        places['type'] = f"{category}:{value}"
                        scenic_points.append(places)
            
            if not scenic_points:
                print("No scenic locations found", file=sys.stderr)
                return []
                
            # Combine all scenic points
            self.scenic_points = pd.concat(scenic_points)
            
            # Project to UTM before calculating centroids
            self.scenic_points = self.scenic_points.to_crs(epsg=32630)
            self.scenic_points['geometry'] = self.scenic_points.geometry.centroid
            # Project back to WGS84
            self.scenic_points = self.scenic_points.to_crs(epsg=4326)
            
            # Add location coordinates and elevation
            self.scenic_points['location'] = self.scenic_points.apply(
                lambda row: (row.geometry.y, row.geometry.x), axis=1
            )
            self.scenic_points['elevation'] = self.scenic_points.get('ele', 0)
            
            # Calculate scenic scores
            self.scenic_points['score'] = self.scenic_points.apply(
                self._calculate_scenic_score, axis=1
            )
            
            print(f"Found {len(self.scenic_points)} scenic locations", file=sys.stderr)
            return self.scenic_points.sort_values('score', ascending=False).to_dict('records')
            
        except Exception as e:
            print(f"Error identifying scenic locations: {str(e)}", file=sys.stderr)
            raise
            
    def _calculate_scenic_score(self, point_data: pd.Series) -> float:
        """Calculate a scenic score based on various factors."""
        score = 0
        
        # Elevation score (higher is better)
        try:
            elevation = float(point_data.get('ele', 0))
        except (ValueError, TypeError):
            elevation = 0.0
            
        score += min(elevation / 100, 5)  # Cap at 5 points
        
        # Type-specific bonuses
        if point_data.get('natural') == 'peak':
            score += 3
        elif point_data.get('natural') == 'waterfall':
            score += 2
        elif point_data.get('tourism') == 'viewpoint':
            score += 2
            
        return score

    def find_feasible_routes(self, start_point: Tuple[float, float], 
                           end_point: Tuple[float, float]) -> Dict:
        """Find feasible hiking routes between two points."""
        try:
            # Find nearest nodes in the graph
            start_node = ox.nearest_nodes(self.graph, start_point[1], start_point[0])
            end_node = ox.nearest_nodes(self.graph, end_point[1], end_point[0])
            
            # Calculate shortest path
            route = nx.shortest_path(
                self.graph, 
                start_node, 
                end_node, 
                weight='length'
            )
            
            # Calculate route length in kilometers
            route_length = sum(
                self.graph[route[i]][route[i+1]][0].get('length', 0)
                for i in range(len(route)-1)
            ) / 1000  # Convert to kilometers
            
            # Calculate straight-line distance for comparison
            straight_line = geodesic(start_point, end_point).kilometers
            
            # If the route is more than 3x the straight-line distance, it's probably not feasible
            if route_length > straight_line * 3:
                return {
                    'route': None,
                    'length': float('inf'),
                    'is_feasible': False
                }
            
            return {
                'route': route,
                'length': route_length,
                'is_feasible': True
            }
        except (nx.NetworkXNoPath, KeyError) as e:
            print(f"Error finding route: {str(e)}", file=sys.stderr)
            return {
                'route': None,
                'length': float('inf'),
                'is_feasible': False
            }

    def get_scenic_towns(self) -> pd.DataFrame:
        """Return a DataFrame of prominent towns/villages that are within 1km of a pub, campsite, or hostel."""
        if self.towns is None:
            self.fetch_towns()
        if not hasattr(self, 'pubs'):
            self.pubs = self.fetch_pubs()
        if not hasattr(self, 'campsites'):
            self.campsites = self.fetch_campsites()
        if not hasattr(self, 'hostels'):
            self.hostels = self.fetch_hostels()
            
        # Filter for towns or villages (not hamlets)
        filtered = self.towns[self.towns['place'].isin(['town', 'village'])]
        
        # Filter for locations near pubs, campsites, or hostels
        towns_with_amenities = []
        for idx, town in filtered.iterrows():
            town_point = (town.geometry.y, town.geometry.x)
            has_amenity = False
            
            # Check if any pub is within 1km
            for _, pub in self.pubs.iterrows():
                pub_point = (pub.geometry.y, pub.geometry.x)
                if geodesic(town_point, pub_point).kilometers <= 1.0:
                    has_amenity = True
                    break
            
            # Check if any campsite is within 1km
            if not has_amenity:
                for _, campsite in self.campsites.iterrows():
                    campsite_point = (campsite.geometry.y, campsite.geometry.x)
                    if geodesic(town_point, campsite_point).kilometers <= 1.0:
                        has_amenity = True
                        break
            
            # Check if any hostel is within 1km
            if not has_amenity:
                for _, hostel in self.hostels.iterrows():
                    hostel_point = (hostel.geometry.y, hostel.geometry.x)
                    if geodesic(town_point, hostel_point).kilometers <= 1.0:
                        has_amenity = True
                        break
            
            if has_amenity:
                towns_with_amenities.append(town)
        
        if not towns_with_amenities:
            print("Warning: No towns/villages found within 1km of a pub, campsite, or hostel.", file=sys.stderr)
            return pd.DataFrame()
            
        return pd.DataFrame(towns_with_amenities).reset_index()

    def _calculate_location_score(self, location_name: str, location_type: str) -> float:
        """Calculate a score for a location based on its prominence and amenities."""
        score = 5.0  # Base score
        
        # Bonus for towns over villages
        if location_type == 'town':
            score += 1.0
            
        return score

    def _is_forward_progress(self, current_point: Tuple[float, float], 
                           next_point: Tuple[float, float], 
                           previous_points: List[Tuple[float, float]]) -> bool:
        """Check if the next point represents forward progress in the journey."""
        if not previous_points:
            return True
            
        # Calculate the general direction of travel from previous points
        prev_lat = sum(p[0] for p in previous_points) / len(previous_points)
        prev_lon = sum(p[1] for p in previous_points) / len(previous_points)
        
        # Calculate vectors
        current_vector = (current_point[0] - prev_lat, current_point[1] - prev_lon)
        next_vector = (next_point[0] - current_point[0], next_point[1] - current_point[1])
        
        # Calculate dot product to determine if moving in similar direction
        dot_product = current_vector[0] * next_vector[0] + current_vector[1] * next_vector[1]
        
        # If dot product is positive, we're moving in a similar direction
        return dot_product > 0

    def generate_itinerary(self, num_days: int = 3, min_km: float = 10, max_km: float = 15, max_retries: int = 5) -> list:
        """Generate a 3-day itinerary starting at a notable Brecon Beacons location."""
        towns_df = self.get_scenic_towns()
        if len(towns_df) < 2:
            print("Not enough prominent towns/villages to generate itinerary.", file=sys.stderr)
            return []

        # Try different starting points until we find a valid route
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} of {max_retries} to generate itinerary...", file=sys.stderr)
            
            # Randomly select a starting town
            start_row = towns_df.iloc[random.randint(0, len(towns_df) - 1)]
            visited_ids = {start_row.name}
            current_point = (start_row.geometry.y, start_row.geometry.x)
            current_name = start_row.get('name', f"Unnamed {start_row['place']}")
            previous_points = []
            
            # Find the first end location for Day 1
            candidates = []
            for idx, row in towns_df.iterrows():
                if row.name in visited_ids:
                    continue
                dest_point = (row.geometry.y, row.geometry.x)
                dest_name = row.get('name', f"Unnamed {row['place']}")
                straight_line_dist = geodesic(current_point, dest_point).kilometers
                if min_km <= straight_line_dist <= max_km:
                    candidates.append((row, straight_line_dist))
            
            if not candidates:
                print(f"No suitable end location found for Day 1 from {current_name}. Trying another starting point...", file=sys.stderr)
                continue
                
            # If we found candidates, proceed with the itinerary
            next_row, distance = random.choice(candidates)
            next_point = (next_row.geometry.y, next_row.geometry.x)
            next_name = next_row.get('name', f"Unnamed {next_row['place']}")
            itinerary = [{
                'day': 1,
                'start': current_name,
                'end': next_name,
                'location': next_point,
                'type': next_row['place'],
                'distance': round(distance, 1),
                'score': self._calculate_location_score(next_name, next_row['place'])
            }]
            previous_points.append(current_point)
            current_point = next_point
            current_name = next_name
            visited_ids.add(next_row.name)

            # Generate remaining days
            for day in range(2, num_days + 1):
                print(f"Planning day {day}...", file=sys.stderr)
                candidates = []
                for idx, row in towns_df.iterrows():
                    if row.name in visited_ids:
                        continue
                    dest_point = (row.geometry.y, row.geometry.x)
                    dest_name = row.get('name', f"Unnamed {row['place']}")
                    straight_line_dist = geodesic(current_point, dest_point).kilometers
                    if min_km <= straight_line_dist <= max_km and self._is_forward_progress(current_point, dest_point, previous_points):
                        candidates.append((row, straight_line_dist))
                if not candidates:
                    print(f"No suitable forward progress location found for day {day}. Trying another starting point...", file=sys.stderr)
                    break
                next_row, distance = random.choice(candidates)
                next_point = (next_row.geometry.y, next_row.geometry.x)
                next_name = next_row.get('name', f"Unnamed {next_row['place']}")
                itinerary.append({
                    'day': day,
                    'start': current_name,
                    'end': next_name,
                    'location': next_point,
                    'type': next_row['place'],
                    'distance': round(distance, 1),
                    'score': self._calculate_location_score(next_name, next_row['place'])
                })
                previous_points.append(current_point)
                current_point = next_point
                current_name = next_name
                visited_ids.add(next_row.name)
            
            # If we successfully generated all days, return the itinerary
            if len(itinerary) == num_days:
                return itinerary
            
            # If we didn't complete all days, continue to next attempt
            print("Could not complete full itinerary. Trying another starting point...", file=sys.stderr)
        
        print(f"Failed to generate a complete itinerary after {max_retries} attempts.", file=sys.stderr)
        return []

    def validate_and_improve_routes(self, itinerary: List[Dict]) -> List[Dict]:
        """Post-process the itinerary to validate and improve hiking routes between points."""
        if not itinerary:
            return []
            
        improved_itinerary = []
        for day in itinerary:
            # Get start and end points from the itinerary
            start_point = None
            end_point = None
            
            # Find coordinates for start point
            if day['start'] in self.accommodations['name'].values:
                start_accommodation = self.accommodations[self.accommodations['name'] == day['start']].iloc[0]
                start_point = (start_accommodation.geometry.y, start_accommodation.geometry.x)
                
            # Find coordinates for end point
            if day['end'] in self.accommodations['name'].values:
                end_accommodation = self.accommodations[self.accommodations['name'] == day['end']].iloc[0]
                end_point = (end_accommodation.geometry.y, end_accommodation.geometry.x)
            
            if not start_point or not end_point:
                print(f"Warning: Could not find coordinates for {day['start']} or {day['end']}", file=sys.stderr)
                improved_itinerary.append(day)
                continue
                
            # Find the best route between points
            route_info = self.find_feasible_routes(start_point, end_point)
            
            if route_info['is_feasible']:
                # Add route details to the day's itinerary
                improved_day = day.copy()
                improved_day.update({
                    'route_length': round(route_info['length'], 1),
                    'route_exists': True,
                    'route_details': {
                        'start_coords': start_point,
                        'end_coords': end_point,
                        'path': route_info['route']
                    }
                })
                
                # Add scenic points along the route
                scenic_points = self._find_scenic_points_along_route(route_info['route'])
                if scenic_points:
                    improved_day['scenic_points'] = scenic_points
                    
                improved_itinerary.append(improved_day)
            else:
                print(f"Warning: No feasible route found between {day['start']} and {day['end']}", file=sys.stderr)
                improved_day = day.copy()
                improved_day.update({
                    'route_exists': False,
                    'route_length': float('inf')
                })
                improved_itinerary.append(improved_day)
                
        return improved_itinerary
        
    def _find_scenic_points_along_route(self, route: List[int]) -> List[Dict]:
        """Find scenic points that are near the route."""
        if not route or not self.scenic_points is not None:
            return []
            
        scenic_points = []
        route_nodes = [self.graph.nodes[node] for node in route]
        
        for _, point in self.scenic_points.iterrows():
            point_coords = point['location']
            # Check if point is within 1km of any node in the route
            for node in route_nodes:
                # Ensure coordinates are in the correct order (lat, lon)
                node_coords = (float(node['y']), float(node['x']))
                try:
                    if geodesic(point_coords, node_coords).kilometers <= 1.0:
                        scenic_points.append({
                            'name': point['name'],
                            'type': point['type'],
                            'location': point_coords,
                            'elevation': point['elevation'],
                            'score': point['score']
                        })
                        break
                except ValueError as e:
                    print(f"Warning: Invalid coordinates encountered: {str(e)}", file=sys.stderr)
                    continue
                    
        return sorted(scenic_points, key=lambda x: x['score'], reverse=True)

    def format_itinerary(self, itinerary: List[Dict]) -> Dict:
        """Format the itinerary as a JSON output."""
        if not itinerary:
            return {"error": "No feasible itinerary found."}
            
        # Validate and improve routes
        improved_itinerary = self.validate_and_improve_routes(itinerary)
            
        return {
            "title": "4-Day Hiking Itinerary in Brecon Beacons",
            "days": improved_itinerary
        }

if __name__ == "__main__":
    try:
        planner = BreconBeaconsPlanner()
        print("Fetching OpenStreetMap data...", file=sys.stderr)
        planner.fetch_osm_data()
        print("Fetching towns and villages...", file=sys.stderr)
        planner.fetch_towns()
        print("Identifying scenic locations...", file=sys.stderr)
        planner.identify_scenic_locations()
        
        # Generate a 3-day itinerary with 10-15km (as the crow flies) per day
        print("Generating itinerary...", file=sys.stderr)
        itinerary = planner.generate_itinerary(num_days=3, min_km=10, max_km=15)
        result = planner.format_itinerary(itinerary)
        print(json.dumps(result))
        sys.stdout.flush()
    except Exception as e:
        error_info = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_info))
        sys.exit(1) 