import { ReactNode } from 'react';
import { SheetHandle } from './SheetHandle';
import { useBottomSheet, SnapPoint, SNAP_HEIGHTS } from '../../hooks/useBottomSheet';

interface BottomSheetProps {
  children: ReactNode;
  snap: SnapPoint;
  onSnapChange: (snap: SnapPoint) => void;
}

export function BottomSheet({ children, snap, onSnapChange }: BottomSheetProps) {
  const { translateY, isDragging, handlers } = useBottomSheet({
    initialSnap: snap,
    onSnapChange,
  });

  // Calculate the height based on snap point
  const height = SNAP_HEIGHTS[snap];

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0
        bg-white rounded-t-3xl shadow-2xl
        ${isDragging ? '' : 'transition-all duration-300 ease-out'}
      `}
      style={{
        height: `${height}vh`,
        transform: `translateY(${translateY}px)`,
        paddingBottom: 'env(safe-area-inset-bottom)',
        zIndex: 1001,
      }}
    >
      {/* Handle */}
      <SheetHandle {...handlers} />

      {/* Content */}
      <div
        className="px-4 pb-4 overflow-y-auto"
        style={{
          height: `calc(100% - 24px - env(safe-area-inset-bottom))`,
        }}
      >
        {children}
      </div>
    </div>
  );
}

export { useBottomSheet, SNAP_HEIGHTS };
export type { SnapPoint };
