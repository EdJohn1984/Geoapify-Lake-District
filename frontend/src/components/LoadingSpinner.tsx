import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message = 'Generating your hiking route...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
      <p className="text-gray-600 text-lg">{message}</p>
      <p className="text-gray-400 text-sm mt-2">This may take a few moments</p>
    </div>
  );
};

export default LoadingSpinner;

