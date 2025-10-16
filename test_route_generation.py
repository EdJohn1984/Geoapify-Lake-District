#!/usr/bin/env python3
"""
Test route generation for a specific region.
"""
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.services.route_planner import RoutePlanner
from backend.regions.registry import region_registry

def test_route_generation(region_id):
    """Test route generation for a specific region."""
    print(f"🧪 Testing route generation for {region_id}...")
    
    try:
        # Initialize route planner
        route_planner = RoutePlanner()
        
        # Generate route with minimal tries
        result = route_planner.generate_route(
            region_id=region_id,
            num_days=3,
            max_tries=2,  # Very minimal for testing
            good_enough_threshold=0.5  # More lenient
        )
        
        if result:
            print(f"✅ Route generated successfully!")
            print(f"📍 Waypoints: {result['waypoints']}")
            print(f"🦵 Legs: {len(result['legs'])}")
            print(f"🌄 Scenic midpoints: {len(result['scenic_midpoints'])}")
            return True
        else:
            print(f"❌ No route generated")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    region_id = sys.argv[1] if len(sys.argv) > 1 else "peak_district"
    test_route_generation(region_id)
