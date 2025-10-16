"""
Integration tests for API endpoints.
"""
import pytest
import json
from unittest.mock import patch, Mock
from backend.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestRegionsAPI:
    """Test regions API endpoints."""
    
    def test_get_regions(self, client):
        """Test GET /api/regions endpoint."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.to_api_format.return_value = [
                {
                    "id": "lake_district",
                    "name": "Lake District",
                    "description": "Mountain hiking routes",
                    "endpoints": {
                        "generate_route": "/api/regions/lake_district/routes",
                        "generate_interactive_route": "/api/regions/lake_district/routes",
                        "route_status": "/api/regions/lake_district/routes"
                    }
                }
            ]
            
            response = client.get('/api/regions')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'regions' in data
            assert len(data['regions']) == 1
            assert data['regions'][0]['id'] == 'lake_district'
    
    def test_get_regions_error(self, client):
        """Test GET /api/regions endpoint with error."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.to_api_format.side_effect = Exception("Test error")
            
            response = client.get('/api/regions')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_get_region_info(self, client):
        """Test GET /api/regions/{region_id} endpoint."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_planner') as mock_planner:
            
            # Mock region
            mock_region = Mock()
            mock_region.id = "lake_district"
            mock_region.name = "Lake District"
            mock_region.description = "Mountain hiking routes"
            mock_region.route_params.default_days = 3
            mock_region.route_params.min_distance_km = 10
            mock_region.route_params.max_distance_km = 15
            
            mock_registry.get_region.return_value = mock_region
            mock_registry.load_waypoints.return_value = [{"properties": {"name": "Test"}}]
            mock_planner._get_scenic_points.return_value = [{"name": "Peak"}]
            
            response = client.get('/api/regions/lake_district')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['region'] == 'lake_district'
            assert data['name'] == 'Lake District'
            assert data['waypoints_count'] == 1
            assert data['scenic_points_count'] == 1
    
    def test_get_region_info_not_found(self, client):
        """Test GET /api/regions/{region_id} endpoint with non-existent region."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.get_region.return_value = None
            
            response = client.get('/api/regions/nonexistent')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_get_region_info_error(self, client):
        """Test GET /api/regions/{region_id} endpoint with error."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.get_region.side_effect = Exception("Test error")
            
            response = client.get('/api/regions/lake_district')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data


class TestRoutesAPI:
    """Test routes API endpoints."""
    
    def test_generate_route(self, client):
        """Test POST /api/regions/{region_id}/routes endpoint."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_job = Mock()
            mock_job.id = "test_job_123"
            mock_queue.enqueue.return_value = mock_job
            
            response = client.post('/api/regions/lake_district/routes')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['job_id'] == 'test_job_123'
            assert data['status'] == 'queued'
            assert data['region'] == 'lake_district'
    
    def test_generate_route_with_params(self, client):
        """Test POST /api/regions/{region_id}/routes endpoint with parameters."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_job = Mock()
            mock_job.id = "test_job_123"
            mock_queue.enqueue.return_value = mock_job
            
            request_data = {
                "num_days": 4,
                "max_tries": 100,
                "good_enough_threshold": 0.05
            }
            
            response = client.post(
                '/api/regions/lake_district/routes',
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['job_id'] == 'test_job_123'
            assert data['status'] == 'queued'
    
    def test_generate_route_region_not_found(self, client):
        """Test POST /api/regions/{region_id}/routes endpoint with non-existent region."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.region_exists.return_value = False
            
            response = client.post('/api/regions/nonexistent/routes')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_generate_route_error(self, client):
        """Test POST /api/regions/{region_id}/routes endpoint with error."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.region_exists.side_effect = Exception("Test error")
            
            response = client.post('/api/regions/lake_district/routes')
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_get_route_status_completed(self, client):
        """Test GET /api/regions/{region_id}/routes/{job_id} endpoint with completed job."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_job = Mock()
            mock_job.is_finished = True
            mock_job.is_failed = False
            mock_job.result = {"status": "success", "data": "test"}
            mock_queue.fetch_job.return_value = mock_job
            
            response = client.get('/api/regions/lake_district/routes/test_job_123')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'completed'
            assert data['result'] == {"status": "success", "data": "test"}
            assert data['region'] == 'lake_district'
    
    def test_get_route_status_failed(self, client):
        """Test GET /api/regions/{region_id}/routes/{job_id} endpoint with failed job."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_job = Mock()
            mock_job.is_finished = False
            mock_job.is_failed = True
            mock_job.exc_info = "Test error"
            mock_queue.fetch_job.return_value = mock_job
            
            response = client.get('/api/regions/lake_district/routes/test_job_123')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'failed'
            assert data['error'] == 'Test error'
            assert data['region'] == 'lake_district'
    
    def test_get_route_status_in_progress(self, client):
        """Test GET /api/regions/{region_id}/routes/{job_id} endpoint with in-progress job."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_job = Mock()
            mock_job.is_finished = False
            mock_job.is_failed = False
            mock_queue.fetch_job.return_value = mock_job
            
            response = client.get('/api/regions/lake_district/routes/test_job_123')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'in_progress'
            assert data['region'] == 'lake_district'
    
    def test_get_route_status_not_found(self, client):
        """Test GET /api/regions/{region_id}/routes/{job_id} endpoint with non-existent job."""
        with patch('backend.app.region_registry') as mock_registry, \
             patch('backend.app.route_queue') as mock_queue:
            
            mock_registry.region_exists.return_value = True
            mock_queue.fetch_job.return_value = None
            
            response = client.get('/api/regions/lake_district/routes/nonexistent_job')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['status'] == 'not_found'
    
    def test_get_route_status_region_not_found(self, client):
        """Test GET /api/regions/{region_id}/routes/{job_id} endpoint with non-existent region."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.region_exists.return_value = False
            
            response = client.get('/api/regions/nonexistent/routes/test_job_123')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data


class TestHealthAPI:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test GET /api/health endpoint."""
        with patch('backend.app.region_registry') as mock_registry:
            mock_registry.list_regions.return_value = [Mock(), Mock()]  # 2 regions
            
            response = client.get('/api/health')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['regions_loaded'] == 2
