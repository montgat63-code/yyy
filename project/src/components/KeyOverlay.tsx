import { useCallback } from 'react';
import type { KeyBinding } from '@/types';
import { KeyIcon } from './KeyIcon';

interface KeyOverlayProps {
  keys: KeyBinding[];
  opacity: number;
  sizeScale: number;
  editMode: boolean;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onDelete: (id: string) => void;
  onDrag: (id: string, xPct: number, yPct: number) => void;
}

export function KeyOverlay({
  keys,
  opacity,
  sizeScale,
  editMode,
  selectedId,
  onSelect,
  onDelete,
  onDrag,
}: KeyOverlayProps) {
  const handleBgClick = useCallback((e: React.MouseEvent) => {
    if (editMode && e.target === e.currentTarget) {
      onSelect(null);
    }
  }, [editMode, onSelect]);

  return (
    <div
      className="absolute inset-0 overflow-hidden"
      onClick={handleBgClick}
    >
      {keys.map(k => (
        <KeyIcon
          key={k.id}
          binding={k}
          opacity={opacity}
          sizeScale={sizeScale}
          editMode={editMode}
          selected={selectedId === k.id}
          onSelect={() => onSelect(k.id)}
          onDelete={() => onDelete(k.id)}
          onDrag={(x, y) => onDrag(k.id, x, y)}
        />
      ))}
    </div>
  );
}
