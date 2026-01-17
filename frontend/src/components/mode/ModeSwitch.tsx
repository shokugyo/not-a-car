import { AppMode } from '../../types/trip';

interface ModeSwitchProps {
  mode: AppMode;
  onChange: (mode: AppMode) => void;
}

export function ModeSwitch({ mode, onChange }: ModeSwitchProps) {
  return (
    <div className="flex bg-gray-100 rounded-full p-0.5">
      <button
        onClick={() => onChange('owner')}
        className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${
          mode === 'owner'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        オーナー
      </button>
      <button
        onClick={() => onChange('user')}
        className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${
          mode === 'user'
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        利用者
      </button>
    </div>
  );
}
