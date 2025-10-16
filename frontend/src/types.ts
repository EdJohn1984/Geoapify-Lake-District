export interface Region {
  id: string;
  name: string;
  description: string;
  endpoints: {
    generate_route: string;
    generate_interactive_route: string;
    route_status: string;
  };
}

export interface RouteData {
  status: string;
  geojson: GeoJSON.FeatureCollection;
  route_summary: RouteSummary;
  message: string;
}

export interface RouteSummary {
  waypoints: string[];
  total_distance_km: number;
  total_duration_min: number;
  scenic_points: string[];
}

export interface DayDetailsProps {
  day: number;
  from: string;
  to: string;
  distance_km: number;
  duration_hours: number;
  scenic_midpoint?: {
    name: string;
    type: string;
    coordinates: [number, number]; // [lon, lat]
  };
  terrain?: TerrainBreakdown;
  surface_data?: {
    primary_surface: string;
    surface_types: string[];
    trail_characteristics: string;
  };
}

export interface TerrainBreakdown {
  mountain: number;
  forest: number;
  coastal: number;
  valley: number;
}

export type JobStatus = 'idle' | 'queued' | 'in_progress' | 'completed' | 'failed';

