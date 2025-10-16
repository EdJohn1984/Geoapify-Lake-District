#!/usr/bin/env python3
"""
Pre-generate cache data for all regions to avoid long wait times on first use.
"""
import sys
import argparse
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.regions.registry import region_registry
from backend.services.route_planner import RoutePlanner
from backend.services.geoapify_client import GeoAPIfyClient
from backend.services.osm_client import OSMClient
from backend.services.cache_service import CacheService

def prepare_region_cache(region_id, force=False):
    """Pre-generate cache data for a specific region."""
    print(f"\n🏔️  Preparing cache for {region_id}...")
    
    try:
        # Initialize services
        geoapify_client = GeoAPIfyClient()
        osm_client = OSMClient()
        cache_service = CacheService()
        route_planner = RoutePlanner()
        
        # Get region info
        region = region_registry.get_region(region_id)
        if not region:
            print(f"❌ Region {region_id} not found")
            return False
        
        # Optionally invalidate caches first
        if force:
            print("🧹 Forcing cache invalidation for region...")
            cache_service.invalidate_region_cache(region_id)

        print(f"📍 Region: {region.name}")
        print(f"📏 Distance range: {region.route_params.min_distance_km}-{region.route_params.max_distance_km}km")
        
        # Load waypoints
        waypoints = region_registry.load_waypoints(region_id)
        total_waypoints = len(waypoints)
        print(f"🎯 Waypoints: {total_waypoints}")
        
        # Generate feasible pairs
        print("🔗 Generating feasible pairs...")
        feasible_pairs = route_planner._get_feasible_pairs(region_id, waypoints)
        print(f"✅ Generated {len(feasible_pairs)} feasible pairs")
        
        # Generate scenic points
        print("🌄 Fetching scenic points...")
        scenic_points = route_planner._get_scenic_points(region_id)
        print(f"✅ Found {len(scenic_points)} scenic points")

        # Validation summary
        try:
            # Recompute the unique keyed waypoint count using the same logic as feasible pairing
            from backend.utils.geometry import geodesic  # placeholder import to keep symmetry
            unique_keys = set()
            for wp in waypoints:
                props = wp.get('properties', {})
                geom = wp.get('geometry', {})
                coords = geom.get('coordinates', [None, None])
                lon, lat = coords[0], coords[1]
                wp_id = props.get('id') or props.get('osm_id') or props.get('ref')
                if not wp_id:
                    name = props.get('name', 'Unnamed')
                    wp_id = f"{name}:{round(lat, 5)},{round(lon, 5)}"
                unique_keys.add((str(wp_id), lat, lon))
            print(f"📊 Unique keyed waypoints: {len(unique_keys)}/{total_waypoints}")
        except Exception:
            pass
        
        print(f"✅ {region.name} cache prepared successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error preparing {region_id}: {e}")
        return False

def main():
    """Pre-generate cache for all regions."""
    parser = argparse.ArgumentParser(description="Prepare region caches (feasible pairs and scenic points)")
    parser.add_argument("region", nargs="?", help="Optional single region ID to prepare")
    parser.add_argument("--force", action="store_true", help="Force invalidate caches before regeneration")
    args = parser.parse_args()

    if args.region:
        print(f"🚀 Pre-generating cache data for region: {args.region}")
    else:
        print("🚀 Pre-generating cache data for all regions...")
    print("This will take a few minutes but will make route generation much faster!")
    
    if args.region:
        # Single region mode
        ok = prepare_region_cache(args.region, force=args.force)
        print("\n🎉 Cache preparation complete!")
        if ok:
            print("✅ Region prepared successfully")
            sys.exit(0)
        else:
            print("❌ Region preparation failed")
            sys.exit(1)
    else:
        # All regions mode
        regions = region_registry.list_regions()
        print(f"📋 Found {len(regions)} regions to prepare")
        
        success_count = 0
        for region in regions:
            if prepare_region_cache(region.id, force=args.force):
                success_count += 1
        
        print(f"\n🎉 Cache preparation complete!")
        print(f"✅ Successfully prepared {success_count}/{len(regions)} regions")
        
        if success_count == len(regions):
            print("🚀 All regions are now ready for fast route generation!")
        else:
            print("⚠️  Some regions failed - check the logs above")

if __name__ == "__main__":
    main()
