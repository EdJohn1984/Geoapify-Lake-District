"""
Unit tests for region model.
"""
import pytest
from backend.models.region import Region, BoundingBox, RouteParams, TerrainDefaults


class TestBoundingBox:
    """Test BoundingBox model."""
    
    def test_bbox_creation(self):
        """Test bounding box creation."""
        bbox = BoundingBox(west=-3.3, south=54.2, east=-2.7, north=54.6)
        assert bbox.west == -3.3
        assert bbox.south == 54.2
        assert bbox.east == -2.7
        assert bbox.north == 54.6
    
    def test_bbox_to_string(self):
        """Test bbox string conversion."""
        bbox = BoundingBox(west=-3.3, south=54.2, east=-2.7, north=54.6)
        assert bbox.to_bbox_string() == "-3.3,54.2,-2.7,54.6"


class TestRouteParams:
    """Test RouteParams model."""
    
    def test_route_params_creation(self):
        """Test route params creation."""
        params = RouteParams(min_distance_km=10, max_distance_km=15, default_days=3)
        assert params.min_distance_km == 10
        assert params.max_distance_km == 15
        assert params.default_days == 3
        assert params.mode == "hike"  # default value


class TestTerrainDefaults:
    """Test TerrainDefaults model."""
    
    def test_terrain_defaults_creation(self):
        """Test terrain defaults creation."""
        terrain = TerrainDefaults(mountain=40, forest=30, coastal=5, valley=25)
        assert terrain.mountain == 40
        assert terrain.forest == 30
        assert terrain.coastal == 5
        assert terrain.valley == 25
    
    def test_terrain_defaults_validation(self):
        """Test terrain defaults validation."""
        # Valid terrain (sums to 100)
        terrain = TerrainDefaults(mountain=40, forest=30, coastal=5, valley=25)
        assert terrain.mountain + terrain.forest + terrain.coastal + terrain.valley == 100
        
        # Invalid terrain (doesn't sum to 100)
        with pytest.raises(ValueError):
            TerrainDefaults(mountain=40, forest=30, coastal=5, valley=20)


class TestRegion:
    """Test Region model."""
    
    def test_region_from_dict(self):
        """Test region creation from dictionary."""
        data = {
            "id": "test_region",
            "name": "Test Region",
            "description": "A test region",
            "bbox": {"west": -3.3, "south": 54.2, "east": -2.7, "north": 54.6},
            "route_params": {"min_distance_km": 10, "max_distance_km": 15, "default_days": 3},
            "terrain_defaults": {"mountain": 40, "forest": 30, "coastal": 5, "valley": 25},
            "scenic_categories": ["natural.mountain.peak"],
            "waypoints_file": "test.json",
            "cache_prefix": "test"
        }
        
        region = Region.from_dict(data)
        assert region.id == "test_region"
        assert region.name == "Test Region"
        assert isinstance(region.bbox, BoundingBox)
        assert isinstance(region.route_params, RouteParams)
        assert isinstance(region.terrain_defaults, TerrainDefaults)
        assert region.scenic_categories == ["natural.mountain.peak"]
        assert region.waypoints_file == "test.json"
        assert region.cache_prefix == "test"
    
    def test_region_to_dict(self):
        """Test region conversion to dictionary."""
        data = {
            "id": "test_region",
            "name": "Test Region",
            "description": "A test region",
            "bbox": {"west": -3.3, "south": 54.2, "east": -2.7, "north": 54.6},
            "route_params": {"min_distance_km": 10, "max_distance_km": 15, "default_days": 3},
            "terrain_defaults": {"mountain": 40, "forest": 30, "coastal": 5, "valley": 25},
            "scenic_categories": ["natural.mountain.peak"],
            "waypoints_file": "test.json",
            "cache_prefix": "test"
        }
        
        region = Region.from_dict(data)
        result = region.to_dict()
        
        assert result["id"] == "test_region"
        assert result["name"] == "Test Region"
        assert result["bbox"]["west"] == -3.3
        assert result["route_params"]["min_distance_km"] == 10
        assert result["terrain_defaults"]["mountain"] == 40
