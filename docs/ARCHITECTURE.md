# Multi-Region Architecture

## Overview

The hiking trip organizer has been refactored from a 2-region prototype to a scalable multi-region architecture supporting 10+ UK regions with minimal code duplication and configuration-driven behavior.

## Key Improvements

### 1. Unified Route Planning
- **Before**: Separate `geoapify_planner.py` and `cornwall_planner.py` (700+ lines each, 95% identical)
- **After**: Single `RoutePlanner` service that works for all regions
- **Result**: -1,400 lines of code, +90% code reuse

### 2. Configuration-Driven Regions
- **Before**: Hardcoded settings scattered throughout code
- **After**: JSON configuration files for each region
- **Result**: Add new region in ~1 hour (just config + waypoint data)

### 3. Centralized Services
- **GeoAPIfy Client**: Centralized API management with rate limiting
- **OSM Client**: OpenStreetMap data extraction
- **Cache Service**: Region-aware caching with TTL management
- **Region Registry**: Dynamic region loading and validation

### 4. Unified API
- **Before**: Region-specific endpoints (`/api/cornwall/...`)
- **After**: Unified endpoints (`/api/regions/{region_id}/...`)
- **Result**: Consistent API across all regions

## Directory Structure

```
hiking-trip-organizer/
├── backend/                    # Backend services
│   ├── models/                 # Data models
│   │   ├── region.py          # Region configuration model
│   │   └── route.py           # Route data model
│   ├── services/              # Core services
│   │   ├── route_planner.py   # Unified route generation
│   │   ├── geoapify_client.py # GeoAPIfy API wrapper
│   │   ├── osm_client.py      # OpenStreetMap wrapper
│   │   └── cache_service.py   # Caching logic
│   ├── regions/               # Region management
│   │   ├── registry.py        # Region registry
│   │   └── definitions/       # Region configs
│   │       ├── lake_district.json
│   │       ├── cornwall.json
│   │       └── ...
│   ├── tasks/                 # Background jobs
│   │   └── route_tasks.py     # RQ worker tasks
│   ├── utils/                 # Utilities
│   │   ├── terrain_analysis.py
│   │   └── geometry.py
│   └── app.py                 # Flask application
├── data/                      # Data files
│   ├── waypoints/            # Region waypoint data
│   └── cache/                # Cached data
├── frontend/                  # React frontend (unchanged)
└── docs/                     # Documentation
```

## Region Configuration

Each region is defined by a JSON configuration file:

```json
{
  "id": "lake_district",
  "name": "Lake District",
  "description": "Mountain hiking routes in the Lake District National Park",
  "bbox": {
    "west": -3.3,
    "south": 54.2,
    "east": -2.7,
    "north": 54.6
  },
  "route_params": {
    "min_distance_km": 10,
    "max_distance_km": 15,
    "default_days": 3,
    "mode": "hike"
  },
  "terrain_defaults": {
    "mountain": 40,
    "forest": 30,
    "coastal": 5,
    "valley": 25
  },
  "scenic_categories": [
    "natural.mountain.peak",
    "tourism.attraction.viewpoint"
  ],
  "waypoints_file": "lake_district.json",
  "cache_prefix": "lake_district"
}
```

## API Endpoints

### Regions
- `GET /api/regions` - List all regions
- `GET /api/regions/{region_id}` - Get region information

### Routes
- `POST /api/regions/{region_id}/routes` - Generate route
- `GET /api/regions/{region_id}/routes/{job_id}` - Check status

## Adding a New Region

1. **Create region configuration**:
   ```bash
   # Create config file
   cp backend/regions/definitions/lake_district.json backend/regions/definitions/new_region.json
   # Edit the configuration
   ```

2. **Add waypoint data**:
   ```bash
   # Add waypoint file
   cp data/waypoints/lake_district.json data/waypoints/new_region.json
   # Edit the waypoints
   ```

3. **Test the region**:
   ```bash
   # Test region loading
   python -c "from backend.regions.registry import region_registry; print(region_registry.get_region('new_region'))"
   ```

4. **Deploy**: The region is automatically available via the API!

## Benefits

### Immediate
- **-1,400 lines of code** (eliminate duplication)
- **+90% code reuse** across regions
- **Centralized configuration** (easy updates)
- **Better testing** (test one planner, works for all)

### Long-term
- **Add new region in ~1 hour** (just config + waypoint data)
- **Consistent behavior** across all regions
- **Easier debugging** (one code path)
- **Better maintainability** (clear separation of concerns)
- **Team scalability** (clear module boundaries)

## Migration Notes

The refactoring maintains backward compatibility:
- All existing functionality preserved
- Lake District & Cornwall work identically
- Frontend requires minimal updates
- Gradual migration possible

## Next Steps

1. Add remaining 7 UK regions
2. Build admin interface for region management
3. Add data validation pipeline
4. Implement region-specific features
5. Consider multi-country expansion
