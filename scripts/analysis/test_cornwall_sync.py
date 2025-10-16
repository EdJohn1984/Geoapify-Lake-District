import requests
import json

def test_cornwall_sync():
    """Test Cornwall API endpoints synchronously (without background jobs)."""
    BASE_URL = "http://localhost:5000"
    
    print("=== Testing Cornwall API (Synchronous) ===")
    
    # Test 1: Get regions info
    print("\n1. Testing /api/regions")
    try:
        response = requests.get(f"{BASE_URL}/api/regions")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Regions endpoint working")
            print(f"   Available regions: {len(data['regions'])}")
            for region in data['regions']:
                print(f"   - {region['name']}: {region['description']}")
        else:
            print(f"❌ Regions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Regions endpoint error: {e}")
    
    # Test 2: Get Cornwall info
    print("\n2. Testing /api/cornwall/info")
    try:
        response = requests.get(f"{BASE_URL}/api/cornwall/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cornwall info endpoint working")
            print(f"   Waypoints: {data['waypoints_count']}")
            print(f"   Scenic points: {data['scenic_points_count']}")
            print(f"   Sample waypoints: {', '.join(data['sample_waypoints'][:5])}")
        else:
            print(f"❌ Cornwall info endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cornwall info endpoint error: {e}")
    
    # Test 3: Test direct route generation (bypassing background jobs)
    print("\n3. Testing direct Cornwall route generation")
    try:
        from route_tasks import generate_cornwall_route
        
        result = generate_cornwall_route()
        
        if result['status'] == 'success':
            print(f"✅ Direct Cornwall route generation successful")
            route = result['route']
            print(f"   Waypoints: {' → '.join(route['waypoints'])}")
            print(f"   Legs: {len(route['legs'])}")
            for i, leg in enumerate(route['legs']):
                print(f"     Day {i+1}: {leg['from']} → {leg['to']} ({leg['distance']:.1f}km)")
        else:
            print(f"❌ Direct Cornwall route generation failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Direct Cornwall route generation error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test direct interactive route generation
    print("\n4. Testing direct Cornwall interactive route generation")
    try:
        from route_tasks import generate_cornwall_interactive_route
        
        result = generate_cornwall_interactive_route()
        
        if result['status'] == 'success':
            print(f"✅ Direct Cornwall interactive route generation successful")
            geojson = result['geojson']
            summary = result['route_summary']
            print(f"   GeoJSON features: {len(geojson['features'])}")
            print(f"   Total distance: {summary['total_distance_km']:.1f} km")
            print(f"   Total duration: {summary['total_duration_min']:.1f} minutes")
            print(f"   Scenic points: {len(summary['scenic_points'])}")
        else:
            print(f"❌ Direct Cornwall interactive route generation failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Direct Cornwall interactive route generation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cornwall_sync()

