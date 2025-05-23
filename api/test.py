from index import app

def test_health_check():
    with app.test_client() as client:
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json == {'status': 'healthy'}

def test_generate_route():
    with app.test_client() as client:
        response = client.post('/api/generate-route', 
                             json={'num_days': 3, 'num_tries': 200})
        assert response.status_code == 200
        data = response.json
        assert 'days' in data
        assert 'map_image' in data 