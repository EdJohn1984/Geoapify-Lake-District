import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

interface RouteMapProps {
  geojson: GeoJSON.FeatureCollection;
}

const RouteMap: React.FC<RouteMapProps> = ({ geojson }) => {
  // Calculate bounds from GeoJSON
  const getBounds = () => {
    const coordinates: [number, number][] = [];
    
    geojson.features.forEach((feature: any) => {
      if (feature.geometry.type === 'Point') {
        coordinates.push([
          feature.geometry.coordinates[1],
          feature.geometry.coordinates[0]
        ]);
      } else if (feature.geometry.type === 'LineString') {
        feature.geometry.coordinates.forEach((coord: number[]) => {
          coordinates.push([coord[1], coord[0]]);
        });
      } else if (feature.geometry.type === 'MultiLineString') {
        feature.geometry.coordinates.forEach((line: number[][]) => {
          line.forEach((coord: number[]) => {
            coordinates.push([coord[1], coord[0]]);
          });
        });
      }
    });

    if (coordinates.length === 0) {
      return [[54.4, -3.0], [54.5, -3.1]] as L.LatLngBoundsExpression;
    }

    return L.latLngBounds(coordinates);
  };

  const waypointIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const scenicIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const startIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [30, 50],
    iconAnchor: [15, 50],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const endIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [30, 50],
    iconAnchor: [15, 50],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  const pointToLayer = (feature: any, latlng: L.LatLng) => {
    const icon = feature.properties.marker_type === 'scenic' ? scenicIcon : waypointIcon;
    return L.marker(latlng, { icon });
  };

  const onEachFeature = (feature: any, layer: any) => {
    if (feature.properties && feature.properties.name) {
      layer.bindPopup(`
        <div class="font-sans">
          <h3 class="font-bold text-lg">${feature.properties.name}</h3>
          <p class="text-sm text-gray-600">${feature.properties.description || ''}</p>
          ${feature.properties.day ? `<p class="text-xs text-gray-500 mt-1">Day ${feature.properties.day}</p>` : ''}
        </div>
      `);
    }
  };

  const style = (feature: any) => {
    if (feature.geometry.type === 'LineString' || feature.geometry.type === 'MultiLineString') {
      // Different colors for each day
      const dayColors = {
        'Day 1': '#0ea5e9', // Blue
        'Day 2': '#10b981', // Green  
        'Day 3': '#f59e0b', // Orange
      };
      
      const dayName = feature.properties.name;
      const color = dayColors[dayName as keyof typeof dayColors] || '#0ea5e9';
      
      return {
        color: color,
        weight: 5,
        opacity: 0.8,
      };
    }
    return {};
  };

  return (
    <div className="relative rounded-lg overflow-hidden shadow-lg h-[500px] w-full">
      <MapContainer
        bounds={getBounds()}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <GeoJSON
          data={geojson}
          pointToLayer={pointToLayer}
          onEachFeature={onEachFeature}
          style={style}
        />
      </MapContainer>
      
      {/* Route Legend */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
        <h4 className="font-semibold text-sm text-gray-700 mb-2">Route Days</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-blue-500 rounded"></div>
            <span className="text-xs text-gray-600">Day 1</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-green-500 rounded"></div>
            <span className="text-xs text-gray-600">Day 2</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-1 bg-orange-500 rounded"></div>
            <span className="text-xs text-gray-600">Day 3</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RouteMap;

