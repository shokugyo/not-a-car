import React from 'react';

interface SheetHandleProps {
  onTouchStart?: (e: React.TouchEvent) => void;
  onTouchMove?: (e: React.TouchEvent) => void;
  onTouchEnd?: (e: React.TouchEvent) => void;
}

export function SheetHandle({ onTouchStart, onTouchMove, onTouchEnd }: SheetHandleProps) {
  return (
    <div
      className="flex justify-center py-3 cursor-grab active:cursor-grabbing touch-none"
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
    </div>
  );
}
