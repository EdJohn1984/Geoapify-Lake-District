"""
OpenStreetMap Overpass API client wrapper.
"""
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass

from ..config import OVERPASS_API_URL


@dataclass
class SurfaceData:
    """Surface data from OSM."""
    surface: str
    highway: str
    tracktype: str
    lat: float
    lon: float


class OSMClient:
    """Client for OpenStreetMap Overpass API."""
    
    def __init__(self, api_url: str = None):
        self.api_url = api_url or OVERPASS_API_URL
    
    def get_surface_data(self, coordinates: List[Tuple[float, float]], sample_size: int = 10) -> List[SurfaceData]:
        """
        Get surface type data along route coordinates.
        
        Args:
            coordinates: List of (lon, lat) coordinate tuples
            sample_size: Number of coordinates to sample for API calls
        
        Returns:
            List of SurfaceData objects
        """
        # Sample coordinates to avoid too many API calls
        if len(coordinates) > sample_size:
            step = len(coordinates) // sample_size
            sample_coords = coordinates[::step]
        else:
            sample_coords = coordinates
        
        surface_data = []
        
        for coord in sample_coords:
            lon, lat = coord
            
            # Overpass API query for ways near this coordinate with surface tags
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way(around:50,{lat},{lon})["surface"];
              way(around:50,{lat},{lon})["highway"];
              way(around:50,{lat},{lon})["tracktype"];
            );
            out tags;
            """
            
            try:
                response = requests.post(
                    self.api_url,
                    data=overpass_query,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for element in data.get('elements', []):
                        tags = element.get('tags', {})
                        
                        surface_data.append(SurfaceData(
                            surface=tags.get('surface', 'unknown'),
                            highway=tags.get('highway', ''),
                            tracktype=tags.get('tracktype', ''),
                            lat=lat,
                            lon=lon
                        ))
                            
            except Exception as e:
                print(f"[LOG] OSM query error for {lat},{lon}: {e}")
                continue
        
        return surface_data
