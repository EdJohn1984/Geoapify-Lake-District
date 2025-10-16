"""
Region registry for loading and managing region configurations.
"""
from pathlib import Path
from typing import Dict, List, Optional
import json

from ..models.region import Region
from ..config import REGIONS_DIR, WAYPOINTS_DIR


class RegionRegistry:
    """Registry for managing hiking regions."""
    
    def __init__(self):
        self._regions: Dict[str, Region] = {}
        self._load_regions()
    
    def _load_regions(self):
        """Load all region configurations from the definitions directory."""
        if not REGIONS_DIR.exists():
            raise FileNotFoundError(f"Regions directory not found: {REGIONS_DIR}")
        
        for config_file in REGIONS_DIR.glob("*.json"):
            try:
                region = Region.from_file(config_file)
                self._regions[region.id] = region
            except Exception as e:
                print(f"Warning: Failed to load region from {config_file}: {e}")
    
    def get_region(self, region_id: str) -> Optional[Region]:
        """Get a region by ID."""
        return self._regions.get(region_id)
    
    def list_regions(self) -> List[Region]:
        """Get all available regions."""
        return list(self._regions.values())
    
    def get_region_ids(self) -> List[str]:
        """Get all region IDs."""
        return list(self._regions.keys())
    
    def region_exists(self, region_id: str) -> bool:
        """Check if a region exists."""
        return region_id in self._regions
    
    def get_waypoints_file_path(self, region_id: str) -> Path:
        """Get the waypoints file path for a region."""
        region = self.get_region(region_id)
        if not region:
            raise ValueError(f"Region not found: {region_id}")
        
        waypoints_file = WAYPOINTS_DIR / region.waypoints_file
        if not waypoints_file.exists():
            raise FileNotFoundError(f"Waypoints file not found: {waypoints_file}")
        
        return waypoints_file
    
    def load_waypoints(self, region_id: str) -> List[Dict]:
        """Load waypoints for a region."""
        waypoints_file = self.get_waypoints_file_path(region_id)
        
        with open(waypoints_file, 'r') as f:
            return json.load(f)
    
    def to_api_format(self) -> List[Dict]:
        """Convert regions to API format for frontend."""
        regions = []
        for region in self.list_regions():
            regions.append({
                "id": region.id,
                "name": region.name,
                "description": region.description,
                "endpoints": {
                    "generate_route": f"/api/regions/{region.id}/routes",
                    "generate_interactive_route": f"/api/regions/{region.id}/routes",
                    "route_status": f"/api/regions/{region.id}/routes"
                }
            })
        return regions


# Global registry instance
region_registry = RegionRegistry()
