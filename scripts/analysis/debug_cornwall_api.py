import requests
import json

def test_simple_endpoints():
    """Test simple endpoints that don't require background jobs."""
    BASE_URL = "http://localhost:5000"
    
    print("=== Testing Simple Endpoints ===")
    
    # Test regions
    try:
        response = requests.get(f"{BASE_URL}/api/regions")
        print(f"Regions: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Regions: {len(data['regions'])}")
    except Exception as e:
        print(f"Regions error: {e}")
    
    # Test Cornwall info
    try:
        response = requests.get(f"{BASE_URL}/api/cornwall/info")
        print(f"Cornwall info: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Waypoints: {data['waypoints_count']}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"Cornwall info error: {e}")

def test_direct_cornwall_route():
    """Test Cornwall route generation directly without API."""
    print("\n=== Testing Direct Cornwall Route Generation ===")
    
    try:
        from cornwall_planner import generate_cornwall_hiking_route
        
        # Load waypoints
        with open('cornwall_waypoints.json', 'r') as f:
            waypoints_data = json.load(f)
        
        waypoint_dict = {wp['properties']['name']: wp for wp in waypoints_data}
        
        # Generate route
        result = generate_cornwall_hiking_route(waypoint_dict, num_days=3, max_tries=10)
        
        if result:
            print(f"✅ Direct route generation successful")
            print(f"   Waypoints: {' → '.join(result['waypoints'])}")
            print(f"   Legs: {len(result['legs'])}")
        else:
            print(f"❌ Direct route generation failed")
            
    except Exception as e:
        print(f"❌ Direct route generation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_endpoints()
    test_direct_cornwall_route()

