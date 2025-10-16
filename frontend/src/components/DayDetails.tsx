import React from 'react';
import { MapPin, Clock, Mountain, Square, Footprints } from 'lucide-react';

interface DayDetailsProps {
  day: number;
  from: string;
  to: string;
  distance_km: number;
  duration_hours: number;
  scenic_midpoint?: {
    name: string;
    type: string;
    coordinates: [number, number];
  };
  terrain?: {
    mountain: number;
    forest: number;
    coastal: number;
    valley: number;
  };
  surface_data?: {
    primary_surface: string;
    surface_types: string[];
    trail_characteristics: string;
  };
}

const DayDetails: React.FC<DayDetailsProps> = ({
  day,
  from,
  to,
  distance_km,
  duration_hours,
  scenic_midpoint,
  surface_data,
}) => {
  const hasSurfaceData = surface_data && surface_data.primary_surface !== 'unknown';

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900">Day {day}</h3>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>{duration_hours.toFixed(1)} hours</span>
        </div>
      </div>

      <div className="space-y-4 mb-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <MapPin className="w-6 h-6 text-green-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-700">Start Point</p>
              <p className="font-bold text-lg text-green-900">{from}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <MapPin className="w-6 h-6 text-orange-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-orange-700">End Point</p>
              <p className="font-bold text-lg text-orange-900">{to}</p>
            </div>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <Mountain className="w-5 h-5 text-primary-600 mt-0.5" />
          <div>
            <p className="text-sm text-gray-500">Distance</p>
            <p className="font-semibold text-gray-900">{distance_km.toFixed(1)} km</p>
          </div>
        </div>

        {scenic_midpoint && (
          <div className="flex items-start gap-3">
            <Mountain className="w-5 h-5 text-orange-600 mt-0.5" />
            <div>
              <p className="text-sm text-gray-500">Scenic Highlight</p>
              <p className="font-semibold text-gray-900">{scenic_midpoint.name}</p>
              <p className="text-xs text-gray-500">{scenic_midpoint.type}</p>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-semibold text-gray-700">Surface Information</p>
          {!hasSurfaceData && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
              Analyzing...
            </span>
          )}
        </div>
        {hasSurfaceData ? (
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <Square className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Primary Surface</p>
                <p className="font-semibold text-gray-900 capitalize">
                  {surface_data.primary_surface}
                </p>
              </div>
            </div>
            
            {surface_data.surface_types && surface_data.surface_types.length > 1 && (
              <div className="flex items-start gap-3">
                <Footprints className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Surface Types</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {surface_data.surface_types.map((surface, index) => (
                      <span
                        key={index}
                        className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full capitalize"
                      >
                        {surface}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex items-start gap-3">
              <Mountain className="w-5 h-5 text-purple-600 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Trail Characteristics</p>
                <p className="font-medium text-gray-900 text-sm">
                  {surface_data.trail_characteristics}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-gray-500">Analyzing surface data from OpenStreetMap...</p>
            <div className="mt-2">
              <div className="animate-pulse flex space-x-4">
                <div className="rounded-full bg-gray-300 h-4 w-4"></div>
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-3 bg-gray-300 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DayDetails;

