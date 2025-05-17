import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from typing import List, Dict, Tuple, Optional
from shapely.geometry import Point, MultiPoint
import json
import sys
import traceback
import random
from abc import ABC, abstractmethod

class BasePlanner(ABC):
    def __init__(self):
        self.graph = None
        self.scenic_points = None
        self.towns = None
        self.accommodations = None
        
    @abstractmethod
    def get_region_bbox(self) -> Tuple[float, float, float, float]:
        """Return the bounding box for the region (south, north, west, east)."""
        pass
        
    @abstractmethod
    def get_region_name(self) -> str:
        """Return the name of the region."""
        pass
        
    @abstractmethod
    def get_notable_locations(self) -> Dict[str, Tuple[float, float]]:
        """Return a dictionary of notable locations in the region."""
        pass
        
    def fetch_osm_data(self):
        """Fetch OpenStreetMap data for the region."""
        try:
            print("Starting to fetch OSM data...", file=sys.stderr)
            bbox = self.get_region_bbox()
            self.graph = ox.graph_from_bbox(
                bbox[1], bbox[0], bbox[2], bbox[3],
                network_type='walk',
                custom_filter='["highway"~"path|track|footway|bridleway|steps"]'
            )
            self.graph = ox.project_graph(self.graph)
            print(f"Successfully fetched OSM data. Graph has {len(self.graph.nodes)} nodes.", file=sys.stderr)
        except Exception as e:
            print(f"Error fetching OSM data: {str(e)}", file=sys.stderr)
            raise

    def fetch_towns(self):
        """Fetch towns and villages in the region."""
        try:
            print("Fetching towns and villages...", file=sys.stderr)
            bbox = self.get_region_bbox()
            towns = ox.features_from_bbox(
                bbox[1], bbox[0], bbox[2], bbox[3],
                tags={'place': ['town', 'village', 'hamlet']}
            )
            
            # Project to UTM before calculating centroids
            towns = towns.to_crs(epsg=32630)  # UTM zone 30N
            towns['geometry'] = towns.geometry.centroid
            # Project back to WGS84
            towns = towns.to_crs(epsg=4326)
            self.towns = towns
            print(f"Found {len(towns)} towns/villages", file=sys.stderr)
            return towns
        except Exception as e:
            print(f"Error fetching towns: {str(e)}", file=sys.stderr)
            raise

    def fetch_accommodations(self):
        """Fetch accommodations in the region."""
        try:
            print("Fetching accommodations...", file=sys.stderr)
            bbox = self.get_region_bbox()
            accommodations = []
            
            # Fetch different types of accommodations
            for amenity in ['hotel', 'hostel', 'guest_house', 'camp_site']:
                places = ox.features_from_bbox(
                    bbox[1], bbox[0], bbox[2], bbox[3],
                    tags={'tourism': amenity}
                )
                if not places.empty:
                    places['type'] = amenity
                    accommodations.append(places)
            
            if accommodations:
                self.accommodations = pd.concat(accommodations)
                # Project to UTM before calculating centroids
                self.accommodations = self.accommodations.to_crs(epsg=32630)
                self.accommodations['geometry'] = self.accommodations.geometry.centroid
                # Project back to WGS84
                self.accommodations = self.accommodations.to_crs(epsg=4326)
                print(f"Found {len(self.accommodations)} accommodations", file=sys.stderr)
            else:
                print("No accommodations found", file=sys.stderr)
                self.accommodations = pd.DataFrame()
                
            return self.accommodations
        except Exception as e:
            print(f"Error fetching accommodations: {str(e)}", file=sys.stderr)
            raise

    def find_feasible_routes(self, start_point: Tuple[float, float], 
                           end_point: Tuple[float, float]) -> Dict:
        """Find feasible hiking route between two points."""
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
        """Generate a multi-day itinerary for the region."""
        towns_df = self.get_scenic_towns()
        if len(towns_df) < 2:
            print("Not enough prominent towns/villages to generate itinerary.", file=sys.stderr)
            return []

        # Start from a notable location if available
        notable_locations = self.get_notable_locations()
        if notable_locations:
            notable_towns = towns_df[towns_df['name'].isin(notable_locations.keys())]
            if len(notable_towns) == 0:
                print("No notable towns found in the dataset.", file=sys.stderr)
                return []
        else:
            notable_towns = towns_df

        # Try different starting points until we find a valid route
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} of {max_retries} to generate itinerary...", file=sys.stderr)
            
            # Randomly select a starting town
            start_row = notable_towns.iloc[random.randint(0, len(notable_towns) - 1)]
            visited_ids = {start_row.name}
            current_point = (start_row.geometry.y, start_row.geometry.x)
            current_name = start_row.get('name', f"Unnamed {start_row['place']}")
            previous_points = []
            
            itinerary = []
            
            # Generate each day's route
            for day in range(1, num_days + 1):
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
            start_point = None
            end_point = None
            
            # Find the coordinates for start and end points
            notable_locations = self.get_notable_locations()
            if day['start'] in notable_locations:
                start_point = notable_locations[day['start']]
            else:
                # Search in towns DataFrame
                start_town = self.towns[self.towns['name'] == day['start']]
                if not start_town.empty:
                    start_point = (start_town.iloc[0].geometry.y, start_town.iloc[0].geometry.x)
                    
            if day['end'] in notable_locations:
                end_point = notable_locations[day['end']]
            else:
                # Search in towns DataFrame
                end_town = self.towns[self.towns['name'] == day['end']]
                if not end_town.empty:
                    end_point = (end_town.iloc[0].geometry.y, end_town.iloc[0].geometry.x)
            
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
            "title": f"Hiking Itinerary in {self.get_region_name()}",
            "days": improved_itinerary
        } 