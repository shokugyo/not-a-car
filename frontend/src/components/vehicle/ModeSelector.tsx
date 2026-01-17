import { Bed, Package, Car, Pause } from 'lucide-react';
import { VehicleMode } from '../../types/vehicle';

interface ModeSelectorProps {
  currentMode: VehicleMode;
  allowedModes: string[];
  onModeChange: (mode: VehicleMode) => void;
  isLoading?: boolean;
}

const availableModes: {
  mode: VehicleMode;
  icon: React.ElementType;
  label: string;
  description: string;
  activeColor: string;
  activeBg: string;
}[] = [
  {
    mode: 'idle',
    icon: Pause,
    label: '待機',
    description: '運用停止',
    activeColor: 'text-gray-700',
    activeBg: 'bg-gray-100 border-gray-300',
  },
  {
    mode: 'accommodation',
    icon: Bed,
    label: '宿泊',
    description: '宿泊施設として',
    activeColor: 'text-purple-700',
    activeBg: 'bg-purple-50 border-purple-300',
  },
  {
    mode: 'delivery',
    icon: Package,
    label: '配送',
    description: '荷物配送用',
    activeColor: 'text-amber-700',
    activeBg: 'bg-amber-50 border-amber-300',
  },
  {
    mode: 'rideshare',
    icon: Car,
    label: 'ライド',
    description: '乗客送迎用',
    activeColor: 'text-blue-700',
    activeBg: 'bg-blue-50 border-blue-300',
  },
];

export function ModeSelector({
  currentMode,
  allowedModes,
  onModeChange,
  isLoading = false,
}: ModeSelectorProps) {
  const handleModeSelect = (mode: VehicleMode) => {
    if (mode !== currentMode && !isLoading && allowedModes.includes(mode)) {
      onModeChange(mode);
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">モード切替</h3>
      <div className="grid grid-cols-4 gap-2">
        {availableModes.map(({ mode, icon: Icon, label, activeColor, activeBg }) => {
          const isActive = currentMode === mode;
          const isAllowed = allowedModes.includes(mode);
          const isDisabled = !isAllowed || isLoading;

          return (
            <button
              key={mode}
              onClick={() => handleModeSelect(mode)}
              disabled={isDisabled}
              className={`
                flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all
                ${isActive
                  ? `${activeBg} ${activeColor}`
                  : isDisabled
                    ? 'bg-gray-50 border-gray-100 text-gray-300 cursor-not-allowed'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
                }
              `}
            >
              <Icon className={`w-5 h-5 mb-1 ${isActive ? activeColor : ''}`} />
              <span className="text-xs font-medium">{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
