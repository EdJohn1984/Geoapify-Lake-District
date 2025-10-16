"""
Unit tests for GeoAPIfy client.
"""
import pytest
from unittest.mock import patch, Mock
import requests

from backend.services.geoapify_client import GeoAPIfyClient, RouteResult


class TestGeoAPIfyClient:
    """Test GeoAPIfyClient service."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = GeoAPIfyClient()
        assert client.api_key is not None
        assert client.base_url == "https://api.geoapify.com/v1"
        assert client.places_url == "https://api.geoapify.com/v2/places"
    
    def test_client_with_custom_api_key(self):
        """Test client with custom API key."""
        client = GeoAPIfyClient(api_key="test_key")
        assert client.api_key == "test_key"
    
    @patch('requests.get')
    def test_get_route_success(self, mock_get):
        """Test successful route retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [{
                'properties': {'distance': 1000, 'time': 3600},
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [[-3.0, 54.0], [-2.9, 54.1]]
                }
            }]
        }
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        waypoints = [(54.0, -3.0), (54.1, -2.9)]
        result = client.get_route(waypoints)
        
        assert result is not None
        assert isinstance(result, RouteResult)
        assert result.properties['distance'] == 1000
        assert result.properties['time'] == 3600
        assert len(result.coords) == 2
        assert result.coords[0] == (-3.0, 54.0)
        assert result.coords[1] == (-2.9, 54.1)
    
    @patch('requests.get')
    def test_get_route_failure(self, mock_get):
        """Test route retrieval failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        waypoints = [(54.0, -3.0), (54.1, -2.9)]
        result = client.get_route(waypoints)
        
        assert result is None
    
    @patch('requests.get')
    def test_get_route_no_features(self, mock_get):
        """Test route retrieval with no features."""
        # Mock response with no features
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'features': []}
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        waypoints = [(54.0, -3.0), (54.1, -2.9)]
        result = client.get_route(waypoints)
        
        assert result is None
    
    def test_get_route_insufficient_waypoints(self):
        """Test route retrieval with insufficient waypoints."""
        client = GeoAPIfyClient()
        
        # Test with no waypoints
        result = client.get_route([])
        assert result is None
        
        # Test with single waypoint
        result = client.get_route([(54.0, -3.0)])
        assert result is None
    
    @patch('requests.get')
    def test_get_scenic_points_success(self, mock_get):
        """Test successful scenic points retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [
                {
                    'properties': {
                        'name': 'Test Peak',
                        'categories': ['natural.mountain.peak']
                    },
                    'geometry': {
                        'coordinates': [-3.0, 54.0]
                    }
                },
                {
                    'properties': {
                        'name': 'Test Viewpoint',
                        'categories': ['tourism.attraction.viewpoint']
                    },
                    'geometry': {
                        'coordinates': [-2.9, 54.1]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        bbox = "-3.3,54.2,-2.7,54.6"
        categories = ["natural.mountain.peak", "tourism.attraction.viewpoint"]
        
        result = client.get_scenic_points(bbox, categories)
        
        assert len(result) == 2
        assert result[0]['name'] == 'Test Peak'
        assert result[0]['type'] == 'Peak'
        assert result[0]['coords'] == [-3.0, 54.0]
        assert result[1]['name'] == 'Test Viewpoint'
        assert result[1]['type'] == 'Viewpoint'
        assert result[1]['coords'] == [-2.9, 54.1]
    
    @patch('requests.get')
    def test_get_scenic_points_failure(self, mock_get):
        """Test scenic points retrieval failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        bbox = "-3.3,54.2,-2.7,54.6"
        categories = ["natural.mountain.peak"]
        
        result = client.get_scenic_points(bbox, categories)
        
        assert result == []
    
    @patch('requests.get')
    def test_get_scenic_points_no_features(self, mock_get):
        """Test scenic points retrieval with no features."""
        # Mock response with no features
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        client = GeoAPIfyClient()
        bbox = "-3.3,54.2,-2.7,54.6"
        categories = ["natural.mountain.peak"]
        
        result = client.get_scenic_points(bbox, categories)
        
        assert result == []
    
    def test_extract_coords_from_geometry_linestring(self):
        """Test coordinate extraction from LineString geometry."""
        client = GeoAPIfyClient()
        
        geometry = {
            'type': 'LineString',
            'coordinates': [[-3.0, 54.0], [-2.9, 54.1], [-2.8, 54.2]]
        }
        
        coords = client._extract_coords_from_geometry(geometry)
        
        assert len(coords) == 3
        assert coords[0] == (-3.0, 54.0)
        assert coords[1] == (-2.9, 54.1)
        assert coords[2] == (-2.8, 54.2)
    
    def test_extract_coords_from_geometry_multilinestring(self):
        """Test coordinate extraction from MultiLineString geometry."""
        client = GeoAPIfyClient()
        
        geometry = {
            'type': 'MultiLineString',
            'coordinates': [
                [[-3.0, 54.0], [-2.9, 54.1]],
                [[-2.8, 54.2], [-2.7, 54.3]]
            ]
        }
        
        coords = client._extract_coords_from_geometry(geometry)
        
        assert len(coords) == 4
        assert coords[0] == (-3.0, 54.0)
        assert coords[1] == (-2.9, 54.1)
        assert coords[2] == (-2.8, 54.2)
        assert coords[3] == (-2.7, 54.3)
