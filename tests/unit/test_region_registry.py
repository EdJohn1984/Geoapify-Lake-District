"""
Unit tests for region registry.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from backend.regions.registry import RegionRegistry
from backend.models.region import Region


class TestRegionRegistry:
    """Test RegionRegistry service."""
    
    def test_region_registry_initialization(self):
        """Test region registry initialization."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir:
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            
            registry = RegionRegistry()
            assert isinstance(registry, RegionRegistry)
            assert registry._regions == {}
    
    def test_load_regions_from_files(self):
        """Test loading regions from configuration files."""
        # Create temporary region config
        region_data = {
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
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test region file
            region_file = Path(temp_dir) / "test_region.json"
            with open(region_file, 'w') as f:
                json.dump(region_data, f)
            
            # Mock the REGIONS_DIR to point to our temp directory
            with patch('backend.regions.registry.REGIONS_DIR', Path(temp_dir)):
                registry = RegionRegistry()
                
                assert len(registry._regions) == 1
                assert "test_region" in registry._regions
                assert registry._regions["test_region"].name == "Test Region"
    
    def test_get_region(self):
        """Test getting a region by ID."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir:
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            
            registry = RegionRegistry()
            
            # Test getting non-existent region
            assert registry.get_region("nonexistent") is None
    
    def test_list_regions(self):
        """Test listing all regions."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir:
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            
            registry = RegionRegistry()
            regions = registry.list_regions()
            assert isinstance(regions, list)
    
    def test_region_exists(self):
        """Test checking if a region exists."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir:
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            
            registry = RegionRegistry()
            assert not registry.region_exists("nonexistent")
    
    def test_get_waypoints_file_path(self):
        """Test getting waypoints file path."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir, \
             patch('backend.regions.registry.WAYPOINTS_DIR') as mock_waypoints_dir:
            
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            mock_waypoints_dir.__truediv__ = lambda self, other: Path(f"data/waypoints/{other}")
            
            registry = RegionRegistry()
            
            # Test with non-existent region
            with pytest.raises(ValueError):
                registry.get_waypoints_file_path("nonexistent")
    
    def test_load_waypoints(self):
        """Test loading waypoints for a region."""
        waypoints_data = [
            {
                "type": "Feature",
                "properties": {"name": "Test Point"},
                "geometry": {"type": "Point", "coordinates": [-3.0, 54.0]}
            }
        ]
        
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir, \
             patch('backend.regions.registry.WAYPOINTS_DIR') as mock_waypoints_dir, \
             patch('builtins.open', mock_open(read_data=json.dumps(waypoints_data))):
            
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            mock_waypoints_dir.__truediv__ = lambda self, other: Path(f"data/waypoints/{other}")
            
            registry = RegionRegistry()
            
            # Test with non-existent region
            with pytest.raises(ValueError):
                registry.load_waypoints("nonexistent")
    
    def test_to_api_format(self):
        """Test converting regions to API format."""
        with patch('backend.regions.registry.REGIONS_DIR') as mock_dir:
            mock_dir.exists.return_value = True
            mock_dir.glob.return_value = []
            
            registry = RegionRegistry()
            api_format = registry.to_api_format()
            
            assert isinstance(api_format, list)
            # Should be empty since no regions loaded
            assert len(api_format) == 0
