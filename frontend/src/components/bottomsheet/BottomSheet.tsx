import { ReactNode } from 'react';
import { SheetHandle } from './SheetHandle';
import { useBottomSheet, SnapPoint, SNAP_HEIGHTS } from '../../hooks/useBottomSheet';

interface BottomSheetProps {
  children: ReactNode;
  snap: SnapPoint;
  onSnapChange: (snap: SnapPoint) => void;
  isDetailMode?: boolean;
  detailContent?: ReactNode;
  maxSnap?: SnapPoint;
}

export function BottomSheet({
  children,
  snap,
  onSnapChange,
  isDetailMode = false,
  detailContent,
  maxSnap = 2,
}: BottomSheetProps) {
  const effectiveMaxSnap = isDetailMode ? 3 : maxSnap;

  const { translateY, isDragging, handlers } = useBottomSheet({
    initialSnap: snap,
    onSnapChange,
    maxSnap: effectiveMaxSnap,
  });

  // Calculate the height based on snap point
  const height = SNAP_HEIGHTS[snap];
  const isFullscreen = snap === 3;

  return (
    <div
      className={`
        fixed bottom-0 left-0 right-0
        bg-white shadow-2xl
        ${isFullscreen ? 'rounded-none' : 'rounded-t-3xl'}
        ${isDragging ? '' : 'transition-all duration-300 ease-out'}
      `}
      style={{
        height: `${height}vh`,
        transform: `translateY(${translateY}px)`,
        paddingBottom: 'env(safe-area-inset-bottom)',
        zIndex: 1001,
      }}
    >
      {/* Handle - hidden in fullscreen mode */}
      {!isFullscreen && <SheetHandle {...handlers} />}

      {/* Content */}
      <div
        className={`overflow-y-auto ${isFullscreen ? 'px-4 pt-safe' : 'px-4 pb-4'}`}
        style={{
          height: isFullscreen
            ? 'calc(100% - env(safe-area-inset-bottom))'
            : 'calc(100% - 24px - env(safe-area-inset-bottom))',
          paddingTop: isFullscreen ? 'env(safe-area-inset-top)' : undefined,
        }}
      >
        {isFullscreen && detailContent ? detailContent : children}
      </div>
    </div>
  );
}

export { useBottomSheet, SNAP_HEIGHTS };
export type { SnapPoint };
