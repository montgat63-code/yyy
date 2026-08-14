import { useRef, useCallback } from 'react';
import {
  Gamepad2, Crosshair, Target, MousePointerClick, Move,
  type LucideIcon,
} from 'lucide-react';
import type { KeyBinding, KeyType } from '@/types';
import { KEY_TYPE_COLORS } from '@/types';

const ICON_MAP: Record<KeyType, LucideIcon> = {
  steer: Gamepad2,
  aim: Crosshair,
  fire: Target,
  tap: MousePointerClick,
  swipe: Move,
};

interface KeyIconProps {
  binding: KeyBinding;
  opacity: number;
  sizeScale: number;
  editMode: boolean;
  selected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onDrag: (xPct: number, yPct: number) => void;
}

export function KeyIcon({
  binding,
  opacity,
  sizeScale,
  editMode,
  selected,
  onSelect,
  onDelete,
  onDrag,
}: KeyIconProps) {
  const iconRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const offset = useRef({ x: 0, y: 0 });

  const Icon = ICON_MAP[binding.type];
  const color = KEY_TYPE_COLORS[binding.type];
  const size = binding.size * sizeScale;

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (!editMode) return;
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    dragging.current = true;
    const parent = iconRef.current?.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const iconRect = iconRef.current!.getBoundingClientRect();
    offset.current = {
      x: e.clientX - iconRect.left,
      y: e.clientY - iconRect.top,
    };
    onSelect();
    void rect;
  }, [editMode, onSelect]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current || !iconRef.current) return;
    const parent = iconRef.current.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const x = e.clientX - rect.left - offset.current.x;
    const y = e.clientY - rect.top - offset.current.y;
    const xPct = Math.max(0, Math.min(100, (x / rect.width) * 100));
    const yPct = Math.max(0, Math.min(100, (y / rect.height) * 100));
    onDrag(xPct, yPct);
  }, [onDrag]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    dragging.current = false;
    try { (e.target as HTMLElement).releasePointerCapture(e.pointerId); } catch { /* noop */ }
  }, []);

  return (
    <div
      ref={iconRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onContextMenu={editMode ? (e) => { e.preventDefault(); e.stopPropagation(); onDelete(); } : undefined}
      style={{
        left: `${binding.x}%`,
        top: `${binding.y}%`,
        width: `${size}px`,
        height: `${size}px`,
        opacity: editMode ? 1 : opacity / 100,
        cursor: editMode ? 'grab' : 'default',
        touchAction: 'none',
      }}
      className={`absolute -translate-x-1/2 -translate-y-1/2 flex items-center justify-center rounded-full transition-shadow ${
        editMode ? 'cursor-grab active:cursor-grabbing' : ''
      } ${selected ? 'ring-2 ring-white ring-offset-2 ring-offset-transparent z-20' : 'z-10'}`}
    >
      <div
        className="absolute inset-0 rounded-full border-2"
        style={{
          borderColor: color,
          backgroundColor: `${color}22`,
          boxShadow: selected ? `0 0 20px ${color}88` : `0 0 10px ${color}44`,
        }}
      />
      <div className="relative flex flex-col items-center justify-center pointer-events-none">
        <Icon size={size * 0.28} color={color} strokeWidth={2.5} />
        <span
          className="text-[10px] font-bold mt-0.5 leading-none"
          style={{ color }}
        >
          {binding.key}
        </span>
        {editMode && (
          <span className="text-[7px] text-slate-400 mt-0.5 leading-none whitespace-nowrap">
            {binding.label}
          </span>
        )}
      </div>
    </div>
  );
}
