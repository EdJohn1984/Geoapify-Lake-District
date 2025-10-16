import React from 'react';
import { Mountain, Waves, Trees, MapPin, Compass } from 'lucide-react';
import { Region } from '../types';

interface RegionSelectorProps {
  regions: Region[];
  selectedRegion: Region | null;
  onSelectRegion: (region: Region) => void;
}

const RegionSelector: React.FC<RegionSelectorProps> = ({
  regions,
  selectedRegion,
  onSelectRegion,
}) => {
  const getRegionIcon = (regionId: string) => {
    switch (regionId) {
      case 'lake_district':
        return <Mountain className="w-12 h-12" />;
      case 'cornwall':
        return <Waves className="w-12 h-12" />;
      case 'yorkshire_dales':
        return <Trees className="w-12 h-12" />;
      case 'snowdonia':
        return <Mountain className="w-12 h-12" />;
      case 'peak_district':
        return <MapPin className="w-12 h-12" />;
      default:
        return <Compass className="w-12 h-12" />;
    }
  };

  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Select Your Region</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {regions.map((region) => (
          <button
            key={region.id}
            onClick={() => onSelectRegion(region)}
            className={`p-6 rounded-lg border-2 transition-all duration-200 text-left ${
              selectedRegion?.id === region.id
                ? 'border-primary-500 bg-primary-50 shadow-lg'
                : 'border-gray-200 bg-white hover:border-primary-300 hover:shadow-md'
            }`}
          >
            <div className="flex items-start gap-4">
              <div className={`${
                selectedRegion?.id === region.id ? 'text-primary-600' : 'text-gray-400'
              }`}>
                {getRegionIcon(region.id)}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {region.name}
                </h3>
                <p className="text-gray-600 text-sm">
                  {region.description}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default RegionSelector;

