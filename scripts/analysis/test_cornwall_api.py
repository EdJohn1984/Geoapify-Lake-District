import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5000"

def test_cornwall_api():
    """Test all Cornwall API endpoints."""
    print("=== Testing Cornwall API Endpoints ===")
    
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
    
    # Test 3: Generate Cornwall route
    print("\n3. Testing /api/cornwall/generate-route")
    try:
        response = requests.post(f"{BASE_URL}/api/cornwall/generate-route")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cornwall route generation queued")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Region: {data['region']}")
            job_id = data['job_id']
        else:
            print(f"❌ Cornwall route generation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cornwall route generation error: {e}")
        return
    
    # Test 4: Check route status
    print(f"\n4. Testing /api/cornwall/route-status/{job_id}")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/api/cornwall/route-status/{job_id}")
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                print(f"   Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print(f"✅ Cornwall route completed!")
                    result = data['result']
                    if result['status'] == 'success':
                        route = result['route']
                        print(f"   Waypoints: {' → '.join(route['waypoints'])}")
                        print(f"   Legs: {len(route['legs'])}")
                        for i, leg in enumerate(route['legs']):
                            print(f"     Day {i+1}: {leg['from']} → {leg['to']} ({leg['distance']:.1f}km)")
                    else:
                        print(f"   Route generation failed: {result['message']}")
                    break
                elif status == 'failed':
                    print(f"❌ Cornwall route failed: {data.get('error', 'Unknown error')}")
                    break
                else:
                    time.sleep(2)  # Wait 2 seconds before next check
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Status check error: {e}")
            break
    else:
        print(f"⚠️  Route generation timed out after {max_attempts * 2} seconds")
    
    # Test 5: Generate Cornwall interactive route
    print("\n5. Testing /api/cornwall/generate-interactive-route")
    try:
        response = requests.post(f"{BASE_URL}/api/cornwall/generate-interactive-route")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Cornwall interactive route generation queued")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Format: {data['format']}")
            print(f"   Region: {data['region']}")
            interactive_job_id = data['job_id']
        else:
            print(f"❌ Cornwall interactive route generation failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cornwall interactive route generation error: {e}")
        return
    
    # Test 6: Check interactive route status
    print(f"\n6. Testing /api/cornwall/route-status/{interactive_job_id}")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/api/cornwall/route-status/{interactive_job_id}")
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                print(f"   Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print(f"✅ Cornwall interactive route completed!")
                    result = data['result']
                    if result['status'] == 'success':
                        geojson = result['geojson']
                        summary = result['route_summary']
                        print(f"   GeoJSON features: {len(geojson['features'])}")
                        print(f"   Total distance: {summary['total_distance_km']:.1f} km")
                        print(f"   Total duration: {summary['total_duration_min']:.1f} minutes")
                        print(f"   Scenic points: {len(summary['scenic_points'])}")
                    else:
                        print(f"   Interactive route generation failed: {result['message']}")
                    break
                elif status == 'failed':
                    print(f"❌ Cornwall interactive route failed: {data.get('error', 'Unknown error')}")
                    break
                else:
                    time.sleep(2)
            else:
                print(f"❌ Interactive status check failed: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Interactive status check error: {e}")
            break
    else:
        print(f"⚠️  Interactive route generation timed out after {max_attempts * 2} seconds")

def test_api_comparison():
    """Compare Lake District and Cornwall API responses."""
    print("\n=== API Comparison Test ===")
    
    # Test both regions
    regions = [
        ("Lake District", "/api/generate-route", "/api/route-status"),
        ("Cornwall", "/api/cornwall/generate-route", "/api/cornwall/route-status")
    ]
    
    for region_name, generate_endpoint, status_endpoint in regions:
        print(f"\nTesting {region_name}:")
        
        # Generate route
        try:
            response = requests.post(f"{BASE_URL}{generate_endpoint}")
            if response.status_code == 200:
                data = response.json()
                job_id = data['job_id']
                print(f"  ✅ Route generation queued (Job: {job_id})")
                
                # Check status
                for attempt in range(10):
                    time.sleep(3)
                    response = requests.get(f"{BASE_URL}{status_endpoint}/{job_id}")
                    if response.status_code == 200:
                        data = response.json()
                        if data['status'] == 'completed':
                            result = data['result']
                            if result['status'] == 'success':
                                route = result['route']
                                print(f"  ✅ Route completed: {' → '.join(route['waypoints'])}")
                                print(f"     Distance: {sum(leg['distance'] for leg in route['legs']):.1f} km")
                                break
                            else:
                                print(f"  ❌ Route failed: {result['message']}")
                                break
                        elif data['status'] == 'failed':
                            print(f"  ❌ Route failed: {data.get('error', 'Unknown error')}")
                            break
                else:
                    print(f"  ⚠️  Route timed out")
            else:
                print(f"  ❌ Route generation failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    print("Cornwall API Testing")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/regions", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status {response.status_code}")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the Flask app first:")
        print("   python app.py")
        exit(1)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        exit(1)
    
    # Run tests
    test_cornwall_api()
    test_api_comparison()
    
    print(f"\n🎉 Cornwall API testing completed!")
    print(f"Check the server logs for detailed information.")

