#!/usr/bin/env python3
"""
Test script for the new unified API.
"""
import requests
import time
import json

API_BASE = "http://localhost:5000"

def test_regions():
    """Test the regions endpoint."""
    print("Testing /api/regions...")
    response = requests.get(f"{API_BASE}/api/regions")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Regions: {[r['id'] for r in data['regions']]}")
    else:
        print(f"Error: {response.text}")
    print()

def test_region_info(region_id):
    """Test the region info endpoint."""
    print(f"Testing /api/regions/{region_id}...")
    response = requests.get(f"{API_BASE}/api/regions/{region_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Region: {data['name']}")
        print(f"Waypoints: {data['waypoints_count']}")
        print(f"Scenic points: {data['scenic_points_count']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_route_generation(region_id):
    """Test route generation."""
    print(f"Testing route generation for {region_id}...")
    response = requests.post(f"{API_BASE}/api/regions/{region_id}/routes")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Job ID: {data['job_id']}")
        print(f"Status: {data['status']}")
        return data['job_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_route_status(region_id, job_id):
    """Test route status checking."""
    print(f"Testing route status for job {job_id}...")
    response = requests.get(f"{API_BASE}/api/regions/{region_id}/routes/{job_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Job status: {data['status']}")
        if data['status'] == 'completed':
            result = data['result']
            print(f"Route waypoints: {result['route_summary']['waypoints']}")
            print(f"Total distance: {result['route_summary']['total_distance_km']:.1f} km")
            print(f"Total duration: {result['route_summary']['total_duration_min']:.1f} min")
        return data['status']
    else:
        print(f"Error: {response.text}")
        return None

if __name__ == "__main__":
    print("Testing new unified API...")
    print("=" * 50)
    
    # Test regions endpoint
    test_regions()
    
    # Test region info
    test_region_info("lake_district")
    test_region_info("cornwall")
    
    # Test route generation (this will be async)
    print("Testing route generation (this may take a while)...")
    job_id = test_route_generation("lake_district")
    
    if job_id:
        # Poll for completion
        print("Polling for route completion...")
        for i in range(30):  # Poll for up to 1 minute
            status = test_route_status("lake_district", job_id)
            if status in ['completed', 'failed']:
                break
            time.sleep(2)
    
    print("=" * 50)
    print("Test complete!")
