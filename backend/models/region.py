"""
Region model and validation.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import json


@dataclass
class BoundingBox:
    """Geographic bounding box for a region."""
    west: float
    south: float
    east: float
    north: float
    
    def to_bbox_string(self) -> str:
        """Convert to GeoAPIfy bbox format: west,south,east,north"""
        return f"{self.west},{self.south},{self.east},{self.north}"


@dataclass
class RouteParams:
    """Route generation parameters for a region."""
    min_distance_km: float
    max_distance_km: float
    default_days: int
    mode: str = "hike"


@dataclass
class TerrainDefaults:
    """Default terrain composition for a region."""
    mountain: int
    forest: int
    coastal: int
    valley: int
    
    def __post_init__(self):
        """Validate that percentages add up to 100."""
        total = self.mountain + self.forest + self.coastal + self.valley
        if total != 100:
            raise ValueError(f"Terrain percentages must sum to 100, got {total}")


@dataclass
class Region:
    """A hiking region configuration."""
    id: str
    name: str
    description: str
    bbox: BoundingBox
    route_params: RouteParams
    terrain_defaults: TerrainDefaults
    scenic_categories: List[str]
    waypoints_file: str
    cache_prefix: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Region":
        """Create Region from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            bbox=BoundingBox(**data["bbox"]),
            route_params=RouteParams(**data["route_params"]),
            terrain_defaults=TerrainDefaults(**data["terrain_defaults"]),
            scenic_categories=data["scenic_categories"],
            waypoints_file=data["waypoints_file"],
            cache_prefix=data["cache_prefix"]
        )
    
    @classmethod
    def from_file(cls, file_path: Path) -> "Region":
        """Load Region from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict:
        """Convert Region to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "bbox": {
                "west": self.bbox.west,
                "south": self.bbox.south,
                "east": self.bbox.east,
                "north": self.bbox.north
            },
            "route_params": {
                "min_distance_km": self.route_params.min_distance_km,
                "max_distance_km": self.route_params.max_distance_km,
                "default_days": self.route_params.default_days,
                "mode": self.route_params.mode
            },
            "terrain_defaults": {
                "mountain": self.terrain_defaults.mountain,
                "forest": self.terrain_defaults.forest,
                "coastal": self.terrain_defaults.coastal,
                "valley": self.terrain_defaults.valley
            },
            "scenic_categories": self.scenic_categories,
            "waypoints_file": self.waypoints_file,
            "cache_prefix": self.cache_prefix
        }
