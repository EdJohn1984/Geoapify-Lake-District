# Cornwall Scenic Midpoints Analysis

## Overview
This document summarizes the scenic midpoint functionality for Cornwall route planning, which is a crucial component of the hiking trip organizer.

## Key Findings

### Scenic Point Coverage
- **Total scenic points**: 100 (90 peaks, 10 viewpoints)
- **Waypoint pairs**: 812 possible combinations
- **Coverage**: 82.0% (666 out of 812 pairs have scenic midpoints within 10km)
- **Status**: ✅ **Excellent coverage** for route planning

### Scenic Point Types
- **Peaks (90)**: Mountain tops, tors, and elevated points
- **Viewpoints (10)**: Designated viewing areas and birdwatching spots

### Most Useful Scenic Points
1. **St Agnes Beacon** - Used in 112 waypoint pairs
2. **Picnic Area** - Used in 94 waypoint pairs  
3. **Tresoweshill** - Used in 64 waypoint pairs
4. **Trink Hill** - Used in 56 waypoint pairs
5. **Carn Marth** - Used in 40 waypoint pairs

## How Scenic Midpoints Work

### 1. Route Planning Process
1. System selects two waypoints for a route leg
2. Calculates geographic midpoint between them
3. Searches for scenic points within 10km of midpoint
4. Selects closest scenic point as route midpoint
5. Routes hiking path through the scenic point

### 2. API Integration
- Uses Geoapify API with `mode=hike` parameter
- Waypoints format: `start_lat,start_lon|scenic_lat,scenic_lon|end_lat,end_lon`
- Ensures routes pass through scenic highlights

### 3. Caching System
- Scenic points cached for 24 hours
- File: `cache/cornwall_scenic_points.json`
- Reduces API calls and improves performance

## Cornwall vs Lake District Comparison

| Metric | Cornwall | Lake District | Ratio |
|--------|----------|---------------|-------|
| Waypoints | 29 | 19 | 1.5x |
| Scenic Points | 100 | 100 | 1.0x |
| Potential Pairs | 812 | 342 | 2.4x |
| Coverage % | 82.0% | ~85%* | Similar |

*Estimated based on Lake District data

## Geographic Distribution

### Coastal Scenic Points
- **St Agnes Beacon** - North coast viewpoint
- **Killigerran Head** - Lizard Peninsula
- **Kynance Cove** - South coast viewpoint
- **Bass Point** - Southernmost point

### Inland Peaks
- **Brown Willy** - Highest point in Cornwall
- **Rough Tor** - Popular hiking destination
- **Carn Marth** - Central Cornwall
- **Kit Hill** - Eastern Cornwall

## Implementation Files

### Data Collection
- `fetch_cornwall_scenic_points.py` - Fetches and caches scenic points
- `cache/cornwall_scenic_points.json` - Cached scenic point data

### Analysis
- `analyze_cornwall_scenic_coverage.py` - Coverage analysis
- `cornwall_scenic_summary.md` - This summary document

### Integration (Next Steps)
- `cornwall_planner.py` - Route planning with scenic midpoints
- `app.py` - API endpoints for Cornwall routes

## Quality Assessment

### Strengths
- ✅ High coverage (82%) ensures most routes have scenic highlights
- ✅ Good mix of peaks and viewpoints
- ✅ Well-distributed across Cornwall geography
- ✅ Includes famous landmarks (St Agnes Beacon, Brown Willy)

### Considerations
- ⚠️ 18% of waypoint pairs lack scenic midpoints (mostly very short distances)
- ⚠️ Some coastal areas may have limited inland scenic points
- ⚠️ Weather-dependent viewpoints may not always be accessible

## Recommendations

1. **Proceed with implementation** - Coverage is excellent
2. **Consider fallback routes** - For pairs without scenic midpoints
3. **Add coastal viewpoints** - Enhance coverage in coastal areas
4. **Monitor performance** - Track route generation success rates

## Next Steps

1. Create `cornwall_planner.py` with scenic midpoint integration
2. Implement Cornwall-specific API endpoints
3. Test route generation with scenic midpoints
4. Validate route quality and user experience

