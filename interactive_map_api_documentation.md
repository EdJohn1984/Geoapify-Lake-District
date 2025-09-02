# Interactive Map API Documentation

## 🗺️ **Interactive Route Generation API**

The hiking trip organizer now supports **interactive map generation** that returns GeoJSON data for use in web-based interactive maps (Leaflet, Mapbox, Google Maps, etc.).

## 📡 **API Endpoints**

### 1. Generate Interactive Route
**Endpoint**: `POST /api/generate-interactive-route`

**Description**: Generates a hiking route and returns GeoJSON data for interactive web maps.

**Request**:
```bash
curl -X POST http://your-domain.com/api/generate-interactive-route
```

**Response**:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "queued",
  "format": "geojson"
}
```

### 2. Check Route Status
**Endpoint**: `GET /api/route-status/<job_id>`

**Description**: Check the status of a route generation job.

**Response (Success)**:
```json
{
  "status": "completed",
  "result": {
    "status": "success",
    "geojson": {
      "type": "FeatureCollection",
      "features": [...]
    },
    "route_summary": {
      "waypoints": ["Borrowdale", "Glenridding", "Elterwater", "Windermere"],
      "total_distance_km": 65.5,
      "total_duration_min": 1204,
      "scenic_points": ["Helvellyn", "Great Rigg", "Black Fell"]
    },
    "message": "Interactive route generated successfully"
  }
}
```

## 🗺️ **GeoJSON Structure**

The returned GeoJSON contains three types of features:

### 1. **Waypoint Features**
```json
{
  "type": "Feature",
  "properties": {
    "name": "Borrowdale",
    "day": 1,
    "type": "waypoint",
    "marker_color": "blue",
    "description": "Day 1 Start"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [-3.123456, 54.789012]
  }
}
```

### 2. **Route Leg Features**
```json
{
  "type": "Feature",
  "properties": {
    "day": 1,
    "distance_km": 15.8,
    "duration_min": 340,
    "type": "route_leg",
    "color": "red",
    "description": "Day 1: 15.8km, 340min"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-3.123456, 54.789012],
      [-3.123457, 54.789013],
      ...
    ]
  }
}
```

### 3. **Scenic Point Features**
```json
{
  "type": "Feature",
  "properties": {
    "name": "Helvellyn",
    "type": "Peak",
    "day": 1,
    "marker_type": "scenic",
    "description": "Scenic Peak: Helvellyn"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [-3.123456, 54.789012]
  }
}
```

## 🌐 **Frontend Integration Examples**

### Leaflet.js Integration
```javascript
// Fetch route data
fetch('/api/generate-interactive-route', {method: 'POST'})
  .then(response => response.json())
  .then(data => {
    // Poll for completion
    pollRouteStatus(data.job_id);
  });

function pollRouteStatus(jobId) {
  fetch(`/api/route-status/${jobId}`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'completed') {
        displayRoute(data.result.geojson);
      } else {
        setTimeout(() => pollRouteStatus(jobId), 2000);
      }
    });
}

function displayRoute(geojson) {
  // Add route to map
  L.geoJSON(geojson, {
    style: function(feature) {
      switch(feature.properties.type) {
        case 'waypoint':
          return {color: feature.properties.marker_color, radius: 8};
        case 'route_leg':
          return {color: feature.properties.color, weight: 4};
        case 'scenic':
          return {color: 'gold', radius: 6};
      }
    },
    onEachFeature: function(feature, layer) {
      layer.bindPopup(feature.properties.description);
    }
  }).addTo(map);
}
```

### Mapbox GL JS Integration
```javascript
// Add GeoJSON source
map.addSource('route', {
  type: 'geojson',
  data: geojsonData
});

// Add route lines
map.addLayer({
  id: 'route-lines',
  type: 'line',
  source: 'route',
  filter: ['==', ['get', 'type'], 'route_leg'],
  paint: {
    'line-color': ['get', 'color'],
    'line-width': 4
  }
});

// Add waypoint markers
map.addLayer({
  id: 'waypoints',
  type: 'circle',
  source: 'route',
  filter: ['==', ['get', 'type'], 'waypoint'],
  paint: {
    'circle-color': ['get', 'marker_color'],
    'circle-radius': 8
  }
});

// Add scenic points
map.addLayer({
  id: 'scenic-points',
  type: 'circle',
  source: 'route',
  filter: ['==', ['get', 'type'], 'scenic'],
  paint: {
    'circle-color': 'gold',
    'circle-radius': 6
  }
});
```

## 🎨 **Styling Guidelines**

### Colors
- **Day 1**: Red (#FF0000)
- **Day 2**: Green (#00FF00)  
- **Day 3**: Purple (#800080)
- **Day 4+**: Orange (#FFA500), Brown (#A52A2A)
- **Waypoints**: Blue, Green, Purple, Orange (cycling)
- **Scenic Points**: Gold (#FFD700)

### Line Weights
- **Route paths**: 4px
- **Day segments**: 2px (for layered effect)

### Marker Sizes
- **Waypoints**: 8-12px radius
- **Scenic points**: 6-8px radius

## 📊 **Route Summary Data**

Each response includes a route summary with:
- **waypoints**: Array of waypoint names in order
- **total_distance_km**: Total route distance in kilometers
- **total_duration_min**: Total estimated duration in minutes
- **scenic_points**: Array of scenic point names

## 🔄 **Asynchronous Processing**

The API uses Redis/RQ for asynchronous processing:
1. **Submit job**: Returns job ID immediately
2. **Poll status**: Check job status every 2-3 seconds
3. **Get result**: Retrieve GeoJSON when completed

## 🚀 **Usage Workflow**

1. **Call API**: `POST /api/generate-interactive-route`
2. **Get job ID**: Store the returned job ID
3. **Poll status**: `GET /api/route-status/<job_id>`
4. **Display route**: Add GeoJSON to your interactive map
5. **Style features**: Apply colors and styles based on feature properties

## 📁 **Example Files**

- `test_route.geojson` - Sample GeoJSON output
- `api_response_example.json` - Complete API response example

The interactive map API provides everything needed to display hiking routes in web-based interactive maps with full zoom, pan, and feature interaction capabilities!
