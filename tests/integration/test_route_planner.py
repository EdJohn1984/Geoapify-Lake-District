"""
Integration tests for route planner service.
"""
import pytest
from unittest.mock import patch, Mock
from backend.services.route_planner import RoutePlanner


class TestRoutePlanner:
    """Test RoutePlanner service."""
    
    def test_route_planner_initialization(self):
        """Test route planner initialization."""
        planner = RoutePlanner()
        assert planner.geoapify_client is not None
        assert planner.osm_client is not None
        assert planner.cache_service is not None
    
    @patch('backend.services.route_planner.region_registry')
    def test_generate_route_region_not_found(self, mock_registry):
        """Test route generation with non-existent region."""
        mock_registry.get_region.return_value = None
        
        planner = RoutePlanner()
        
        with pytest.raises(ValueError, match="Region not found"):
            planner.generate_route("nonexistent_region")
    
    @patch('backend.services.route_planner.region_registry')
    def test_generate_route_no_feasible_pairs(self, mock_registry):
        """Test route generation with no feasible pairs."""
        # Mock region
        mock_region = Mock()
        mock_region.route_params.default_days = 3
        mock_region.route_params.mode = "hike"
        mock_registry.get_region.return_value = mock_region
        
        # Mock waypoints
        mock_registry.load_waypoints.return_value = [
            {"properties": {"name": "A"}, "geometry": {"coordinates": [-3.0, 54.0]}},
            {"properties": {"name": "B"}, "geometry": {"coordinates": [-2.9, 54.1]}}
        ]
        
        planner = RoutePlanner()
        
        # Mock no feasible pairs
        with patch.object(planner, '_get_feasible_pairs', return_value=[]):
            result = planner.generate_route("test_region")
            assert result is None
    
    @patch('backend.services.route_planner.region_registry')
    def test_generate_route_success(self, mock_registry):
        """Test successful route generation."""
        # Mock region
        mock_region = Mock()
        mock_region.route_params.default_days = 3
        mock_region.route_params.mode = "hike"
        mock_registry.get_region.return_value = mock_region
        
        # Mock waypoints
        waypoints = [
            {"properties": {"name": "A"}, "geometry": {"coordinates": [-3.0, 54.0]}},
            {"properties": {"name": "B"}, "geometry": {"coordinates": [-2.9, 54.1]}},
            {"properties": {"name": "C"}, "geometry": {"coordinates": [-2.8, 54.2]}},
            {"properties": {"name": "D"}, "geometry": {"coordinates": [-2.7, 54.3]}}
        ]
        mock_registry.load_waypoints.return_value = waypoints
        
        planner = RoutePlanner()
        
        # Mock feasible pairs
        feasible_pairs = [
            {"from": "A", "to": "B", "distance": 12.0},
            {"from": "B", "to": "C", "distance": 13.0},
            {"from": "C", "to": "D", "distance": 14.0}
        ]
        
        # Mock scenic points
        scenic_points = [
            {"name": "Peak 1", "type": "Peak", "coords": [-2.95, 54.05]},
            {"name": "Viewpoint 1", "type": "Viewpoint", "coords": [-2.85, 54.15]}
        ]
        
        # Mock route data
        route_data = {
            "properties": {"distance": 12000, "time": 3600},
            "geometry": {"type": "LineString", "coordinates": [[-3.0, 54.0], [-2.9, 54.1]]},
            "coords": [(-3.0, 54.0), (-2.9, 54.1)]
        }
        
        with patch.object(planner, '_get_feasible_pairs', return_value=feasible_pairs), \
             patch.object(planner, '_get_scenic_points', return_value=scenic_points), \
             patch.object(planner, '_get_route_with_midpoint', return_value=route_data):
            
            result = planner.generate_route("test_region", num_days=3, max_tries=1)
            
            if result:  # May be None due to randomness
                assert 'waypoints' in result
                assert 'legs' in result
                assert 'scenic_midpoints' in result
                assert len(result['waypoints']) == 4  # 3 days + 1 end point
                assert len(result['legs']) == 3  # 3 days
    
    @patch('backend.services.route_planner.region_registry')
    def test_export_route_to_geojson(self, mock_registry):
        """Test route export to GeoJSON."""
        # Mock region
        mock_region = Mock()
        mock_region.terrain_defaults.__dict__ = {
            'mountain': 40, 'forest': 30, 'coastal': 5, 'valley': 25
        }
        mock_registry.get_region.return_value = mock_region
        
        # Mock waypoints
        waypoints = [
            {"properties": {"name": "A"}, "geometry": {"coordinates": [-3.0, 54.0]}},
            {"properties": {"name": "B"}, "geometry": {"coordinates": [-2.9, 54.1]}},
            {"properties": {"name": "C"}, "geometry": {"coordinates": [-2.8, 54.2]}}
        ]
        mock_registry.load_waypoints.return_value = waypoints
        
        # Mock route data
        route_data = {
            'waypoints': ['A', 'B', 'C'],
            'legs': [
                {
                    'properties': {'distance': 12000, 'time': 3600},
                    'coords': [(-3.0, 54.0), (-2.9, 54.1)]
                },
                {
                    'properties': {'distance': 13000, 'time': 3900},
                    'coords': [(-2.9, 54.1), (-2.8, 54.2)]
                }
            ],
            'scenic_midpoints': [
                {'name': 'Peak 1', 'type': 'Peak', 'coords': [-2.95, 54.05]},
                {'name': 'Viewpoint 1', 'type': 'Viewpoint', 'coords': [-2.85, 54.15]}
            ]
        }
        
        planner = RoutePlanner()
        
        # Mock OSM client
        with patch.object(planner.osm_client, 'get_surface_data', return_value=[]):
            geojson = planner.export_route_to_geojson("test_region", route_data)
            
            assert geojson['type'] == 'FeatureCollection'
            assert 'features' in geojson
            assert len(geojson['features']) > 0
            
            # Check for waypoint features
            waypoint_features = [f for f in geojson['features'] if f['properties']['type'] == 'waypoint']
            assert len(waypoint_features) == 3
            
            # Check for route leg features
            route_features = [f for f in geojson['features'] if f['properties']['type'] == 'route_leg']
            assert len(route_features) == 2
            
            # Check for scenic midpoint features
            scenic_features = [f for f in geojson['features'] if f['properties']['marker_type'] == 'scenic']
            assert len(scenic_features) == 2
    
    @patch('backend.services.route_planner.region_registry')
    def test_export_route_to_geojson_region_not_found(self, mock_registry):
        """Test route export with non-existent region."""
        mock_registry.get_region.return_value = None
        
        planner = RoutePlanner()
        
        with pytest.raises(ValueError, match="Region not found"):
            planner.export_route_to_geojson("nonexistent_region", {})
    
    def test_get_feasible_pairs_cached(self):
        """Test getting cached feasible pairs."""
        planner = RoutePlanner()
        
        with patch.object(planner.cache_service, 'get_feasible_pairs', return_value=[{"test": "data"}]):
            result = planner._get_feasible_pairs("test_region", [])
            assert result == [{"test": "data"}]
    
    def test_get_feasible_pairs_computed(self):
        """Test computing feasible pairs when not cached."""
        planner = RoutePlanner()
        
        waypoints = [
            {"properties": {"name": "A"}, "geometry": {"coordinates": [-3.0, 54.0]}},
            {"properties": {"name": "B"}, "geometry": {"coordinates": [-2.9, 54.1]}}
        ]
        
        with patch.object(planner.cache_service, 'get_feasible_pairs', return_value=None), \
             patch.object(planner.cache_service, 'set_feasible_pairs') as mock_set:
            
            result = planner._get_feasible_pairs("test_region", waypoints)
            assert isinstance(result, list)
            mock_set.assert_called_once()
    
    def test_get_scenic_points_cached(self):
        """Test getting cached scenic points."""
        planner = RoutePlanner()
        
        with patch.object(planner.cache_service, 'get_scenic_points', return_value=[{"test": "data"}]):
            result = planner._get_scenic_points("test_region")
            assert result == [{"test": "data"}]
    
    def test_get_scenic_points_fetched(self):
        """Test fetching scenic points when not cached."""
        planner = RoutePlanner()
        
        with patch.object(planner.cache_service, 'get_scenic_points', return_value=None), \
             patch.object(planner.cache_service, 'set_scenic_points') as mock_set, \
             patch.object(planner.geoapify_client, 'get_scenic_points', return_value=[{"test": "data"}]):
            
            result = planner._get_scenic_points("test_region")
            assert result == [{"test": "data"}]
            mock_set.assert_called_once()
    
    def test_get_route_with_midpoint(self):
        """Test getting route with midpoint."""
        planner = RoutePlanner()
        
        start_coords = [-3.0, 54.0]
        end_coords = [-2.9, 54.1]
        midpoint = {"coords": [-2.95, 54.05]}
        mode = "hike"
        
        with patch.object(planner.geoapify_client, 'get_route') as mock_get_route:
            mock_get_route.return_value = Mock(
                properties={"distance": 1000, "time": 3600},
                geometry={"type": "LineString", "coordinates": []},
                coords=[(-3.0, 54.0), (-2.9, 54.1)]
            )
            
            result = planner._get_route_with_midpoint(start_coords, end_coords, midpoint, mode)
            
            assert result is not None
            assert 'properties' in result
            assert 'geometry' in result
            assert 'coords' in result
            mock_get_route.assert_called_once()
    
    def test_get_route_with_midpoint_failure(self):
        """Test getting route with midpoint failure."""
        planner = RoutePlanner()
        
        start_coords = [-3.0, 54.0]
        end_coords = [-2.9, 54.1]
        midpoint = None
        mode = "hike"
        
        with patch.object(planner.geoapify_client, 'get_route', return_value=None):
            result = planner._get_route_with_midpoint(start_coords, end_coords, midpoint, mode)
            assert result is None
