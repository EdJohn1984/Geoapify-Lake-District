"""
Test configuration and fixtures.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        
        # Create subdirectories
        (data_dir / "waypoints").mkdir()
        (data_dir / "cache" / "scenic_points").mkdir(parents=True)
        (data_dir / "cache" / "feasible_pairs").mkdir(parents=True)
        
        yield data_dir


@pytest.fixture
def sample_region_config():
    """Sample region configuration for testing."""
    return {
        "id": "test_region",
        "name": "Test Region",
        "description": "A test region for unit testing",
        "bbox": {
            "west": -3.3,
            "south": 54.2,
            "east": -2.7,
            "north": 54.6
        },
        "route_params": {
            "min_distance_km": 10,
            "max_distance_km": 15,
            "default_days": 3,
            "mode": "hike"
        },
        "terrain_defaults": {
            "mountain": 40,
            "forest": 30,
            "coastal": 5,
            "valley": 25
        },
        "scenic_categories": [
            "natural.mountain.peak",
            "tourism.attraction.viewpoint"
        ],
        "waypoints_file": "test_region.json",
        "cache_prefix": "test_region"
    }


@pytest.fixture
def sample_waypoints():
    """Sample waypoints data for testing."""
    return [
        {
            "type": "Feature",
            "properties": {
                "name": "Test Point A",
                "country": "United Kingdom",
                "state": "England"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-3.0, 54.0]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Test Point B",
                "country": "United Kingdom",
                "state": "England"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-2.9, 54.1]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Test Point C",
                "country": "United Kingdom",
                "state": "England"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-2.8, 54.2]
            }
        }
    ]


@pytest.fixture
def sample_scenic_points():
    """Sample scenic points data for testing."""
    return [
        {
            "name": "Test Peak",
            "type": "Peak",
            "coords": [-2.95, 54.05]
        },
        {
            "name": "Test Viewpoint",
            "type": "Viewpoint",
            "coords": [-2.85, 54.15]
        }
    ]


@pytest.fixture
def sample_feasible_pairs():
    """Sample feasible pairs data for testing."""
    return [
        {
            "from": "Test Point A",
            "to": "Test Point B",
            "distance": 12.5
        },
        {
            "from": "Test Point B",
            "to": "Test Point C",
            "distance": 13.2
        }
    ]


@pytest.fixture
def mock_region_registry():
    """Mock region registry for testing."""
    with patch('backend.regions.registry.region_registry') as mock_registry:
        yield mock_registry


@pytest.fixture
def mock_route_planner():
    """Mock route planner for testing."""
    with patch('backend.services.route_planner.RoutePlanner') as mock_planner:
        yield mock_planner


@pytest.fixture
def mock_geoapify_client():
    """Mock GeoAPIfy client for testing."""
    with patch('backend.services.geoapify_client.GeoAPIfyClient') as mock_client:
        yield mock_client


@pytest.fixture
def mock_osm_client():
    """Mock OSM client for testing."""
    with patch('backend.services.osm_client.OSMClient') as mock_client:
        yield mock_client


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    with patch('backend.services.cache_service.CacheService') as mock_service:
        yield mock_service
