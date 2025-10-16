import React, { useEffect, useState } from 'react';
import { Mountain } from 'lucide-react';
import RegionSelector from './components/RegionSelector';
import RouteMap from './components/RouteMap';
import DayDetails from './components/DayDetails';
import LoadingSpinner from './components/LoadingSpinner';
import { api } from './services/api';
import { Region, RouteData, DayDetailsProps, JobStatus } from './types';

function App() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus>('idle');
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  useEffect(() => {
    // Load available regions
    api.getRegions().then(setRegions).catch(console.error);
  }, []);

  useEffect(() => {
    if (currentJobId && selectedRegion && jobStatus === 'in_progress') {
      const interval = setInterval(async () => {
        try {
          const status = await api.getRouteStatus(selectedRegion, currentJobId);
          
          if (status.status === 'completed') {
            setRouteData(status.result);
            setJobStatus('completed');
            setCurrentJobId(null);
          } else if (status.status === 'failed') {
            setError('Failed to generate route. Please try again.');
            setJobStatus('failed');
            setCurrentJobId(null);
          }
        } catch (err) {
          console.error('Error checking job status:', err);
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [currentJobId, selectedRegion, jobStatus]);

  const handleGenerateRoute = async () => {
    if (!selectedRegion) return;

    setJobStatus('queued');
    setError(null);
    setRouteData(null);

    try {
      console.log('Starting route generation for region:', selectedRegion.id);
      const response = await api.generateRoute(selectedRegion);
      console.log('API response:', response);
      
      // Check if this is a synchronous response (Cornwall) or async (Lake District)
      if (response.status === 'completed' && response.result) {
        // Synchronous response - Cornwall
        console.log('Handling synchronous response (Cornwall)');
        setRouteData(response.result);
        setJobStatus('completed');
        setCurrentJobId(null); // Clear job ID for synchronous response
      } else if (response.job_id) {
        // Asynchronous response - Lake District
        console.log('Handling asynchronous response (Lake District)');
        setCurrentJobId(response.job_id);
        setJobStatus('in_progress');
      } else {
        console.error('Unexpected response format:', response);
        throw new Error('Unexpected response format');
      }
    } catch (err) {
      console.error('Error generating route:', err);
      setError('Failed to start route generation. Please try again.');
      setJobStatus('failed');
    }
  };

  const getDayDetails = (): DayDetailsProps[] => {
    if (!routeData || !routeData.geojson) return [];

    const details: DayDetailsProps[] = [];
    const waypoints = routeData.route_summary.waypoints;
    const scenicPoints = routeData.route_summary.scenic_points;

    // Extract route legs from GeoJSON (handle both LineString and MultiLineString)
    const routeLegs = routeData.geojson.features.filter(
      (f: any) => f.geometry.type === 'LineString' || f.geometry.type === 'MultiLineString'
    );

    // Sort by day name to ensure correct order
    routeLegs.sort((a: any, b: any) => {
      const dayA = parseInt(a.properties.name?.replace('Day ', '') || '0');
      const dayB = parseInt(b.properties.name?.replace('Day ', '') || '0');
      return dayA - dayB;
    });

    // Build a lookup of scenic midpoint features by day
    const scenicByDay: Record<number, { name: string; type: string; coordinates: [number, number] }> = {};
    routeData.geojson.features
      .filter((f: any) => f.properties?.marker_type === 'scenic' && typeof f.properties?.day === 'number')
      .forEach((f: any) => {
        const d = f.properties.day as number;
        const coords = f.geometry?.coordinates as [number, number];
        scenicByDay[d] = {
          name: f.properties.name,
          type: f.properties.type,
          coordinates: coords,
        };
      });

    routeLegs.forEach((leg: any, index: number) => {
      const distance = leg.properties.distance_km || 0;
      const durationMin = leg.properties.duration_min || 0;
      const surfaceData = leg.properties.surface_data;

      // Extract surface data for display
      let surfaceInfo = undefined;
      if (surfaceData) {
        surfaceInfo = {
          primary_surface: surfaceData.primary_surface || 'unknown',
          surface_types: surfaceData.surface_types || [],
          trail_characteristics: surfaceData.trail_characteristics || 'mixed terrain'
        };
      }

      // For Cornwall routes, we need to map waypoints to days
      // The waypoints array should correspond to the start/end points of each day
      const fromWaypoint = waypoints[index] || `Start Day ${index + 1}`;
      const toWaypoint = waypoints[index + 1] || `End Day ${index + 1}`;

      details.push({
        day: index + 1,
        from: fromWaypoint,
        to: toWaypoint,
        distance_km: distance,
        duration_hours: durationMin / 60,
        scenic_midpoint: scenicByDay[index + 1] || (scenicPoints[index]
          ? { name: scenicPoints[index], type: 'Scenic Point', coordinates: [0, 0] as [number, number] }
          : undefined),
        surface_data: surfaceInfo,
      });
    });

    return details;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Mountain className="w-12 h-12 text-primary-600" />
            <h1 className="text-4xl font-bold text-gray-900">Hiking Trip Organizer</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Plan your perfect multi-day hiking adventure with scenic routes
          </p>
        </div>

        {/* Region Selection */}
        <RegionSelector
          regions={regions}
          selectedRegion={selectedRegion}
          onSelectRegion={setSelectedRegion}
        />

        {/* Generate Button */}
        {selectedRegion && (
          <div className="text-center mb-8">
            <button
              onClick={handleGenerateRoute}
              disabled={jobStatus === 'in_progress' || jobStatus === 'queued'}
              className="px-8 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              {jobStatus === 'in_progress' || jobStatus === 'queued'
                ? 'Generating Route...'
                : 'Generate Hiking Route'}
            </button>
          </div>
        )}

        {/* Loading State */}
        {(jobStatus === 'queued' || jobStatus === 'in_progress') && (
          <LoadingSpinner />
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Route Display */}
        {routeData && routeData.geojson && jobStatus === 'completed' && (
          <div className="space-y-8">
            {/* Route Summary */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Route</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-primary-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Total Distance</p>
                  <p className="text-2xl font-bold text-primary-700">
                    {routeData.route_summary.total_distance_km.toFixed(1)} km
                  </p>
                </div>
                <div className="bg-primary-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Total Duration</p>
                  <p className="text-2xl font-bold text-primary-700">
                    {(routeData.route_summary.total_duration_min / 60).toFixed(1)} hours
                  </p>
                </div>
                <div className="bg-primary-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Days</p>
                  <p className="text-2xl font-bold text-primary-700">
                    {routeData.route_summary.waypoints.length - 1}
                  </p>
                </div>
              </div>
            </div>

            {/* Interactive Map */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Route Map</h2>
              <RouteMap geojson={routeData.geojson} />
            </div>

            {/* Day-by-Day Details */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Daily Itinerary</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {getDayDetails().map((day) => (
                  <DayDetails key={day.day} {...day} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
