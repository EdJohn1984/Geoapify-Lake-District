"""
GeoAPIfy API client wrapper.
"""
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..config import GEOAPIFY_API_KEY


@dataclass
class RouteResult:
    """Result from GeoAPIfy routing API."""
    properties: Dict
    geometry: Dict
    coords: List[Tuple[float, float]]


class GeoAPIfyClient:
    """Client for GeoAPIfy API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEOAPIFY_API_KEY
        self.base_url = "https://api.geoapify.com/v1"
        self.places_url = "https://api.geoapify.com/v2/places"
    
    def get_route(self, waypoints: List[Tuple[float, float]], mode: str = "hike") -> Optional[RouteResult]:
        """
        Get route between waypoints.
        
        Args:
            waypoints: List of (lat, lon) tuples
            mode: Routing mode (hike, drive, etc.)
        
        Returns:
            RouteResult or None if failed
        """
        if len(waypoints) < 2:
            return None
        
        # Format waypoints for API
        wp_str = "|".join([f"{lat},{lon}" for lat, lon in waypoints])
        
        url = f"{self.base_url}/routing"
        params = {
            "waypoints": wp_str,
            "mode": mode,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data.get('features'):
                return None
            
            feature = data['features'][0]
            coords = self._extract_coords_from_geometry(feature['geometry'])
            
            return RouteResult(
                properties=feature['properties'],
                geometry=feature['geometry'],
                coords=coords
            )
            
        except Exception as e:
            print(f"[LOG] GeoAPIfy routing error: {e}")
            return None
    
    def get_scenic_points(self, bbox: str, categories: List[str], limit: int = 100) -> List[Dict]:
        """
        Get scenic points within bounding box.
        
        Args:
            bbox: Bounding box string (west,south,east,north)
            categories: List of category filters
            limit: Maximum number of results
        
        Returns:
            List of scenic point data
        """
        url = self.places_url
        params = {
            "categories": ",".join(categories),
            "filter": f"rect:{bbox}",
            "limit": limit,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'features' not in data:
                return []
            
            scenic_points = []
            for feature in data['features']:
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                
                # Determine scenic type
                scenic_type = 'Peak' if 'natural.mountain.peak' in props.get('categories', []) else 'Viewpoint'
                
                scenic_points.append({
                    'name': props.get('name', 'Unnamed Point'),
                    'type': scenic_type,
                    'coords': [coords[0], coords[1]]  # [lon, lat]
                })
            
            return scenic_points
            
        except Exception as e:
            print(f"[LOG] GeoAPIfy places error: {e}")
            return []
    
    def _extract_coords_from_geometry(self, geometry: Dict) -> List[Tuple[float, float]]:
        """Extract coordinates from GeoJSON geometry."""
        coords = []
        
        if geometry['type'] == 'LineString':
            coords = [(float(pt[0]), float(pt[1])) for pt in geometry['coordinates']]
        elif geometry['type'] == 'MultiLineString':
            for line in geometry['coordinates']:
                coords.extend([(float(pt[0]), float(pt[1])) for pt in line])
        
        return coords
