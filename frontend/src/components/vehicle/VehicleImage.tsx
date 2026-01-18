import { useState } from 'react';
import { Car, Loader2 } from 'lucide-react';

interface VehicleImageProps {
  vehicleId: number;
  modelName: string | null;
  className?: string;
}

export function VehicleImage({
  vehicleId,
  modelName,
  className = '',
}: VehicleImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // 画像パス: /images/vehicles/{vehicleId}.jpg
  // 画像がない場合はフォールバック表示
  const imagePath = `/images/vehicles/${vehicleId}.jpg`;

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    if (!hasError) {
      setHasError(true);
      setIsLoading(false);
    }
  };

  return (
    <div className={`relative rounded-2xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 ${className}`}>
      {/* Loading State */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
        </div>
      )}

      {/* Error Fallback */}
      {hasError ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Car className="w-24 h-24 text-gray-300" strokeWidth={1} />
          <p className="text-gray-400 text-sm mt-2">{modelName || '車両'}</p>
        </div>
      ) : (
        <img
          src={imagePath}
          alt={modelName || `車両 ${vehicleId}`}
          className="w-full h-full object-cover"
          onLoad={handleLoad}
          onError={handleError}
        />
      )}

      {/* Model Name Badge */}
      {modelName && !hasError && !isLoading && (
        <div className="absolute bottom-3 left-3 px-3 py-1 bg-black/50 backdrop-blur-sm rounded-full">
          <span className="text-white text-sm font-medium">{modelName}</span>
        </div>
      )}
    </div>
  );
}
