import { X, Gamepad2, Crosshair, Target, MousePointerClick, Move, Keyboard } from 'lucide-react';

interface HelpModalProps {
  open: boolean;
  onClose: () => void;
}

const HELP_SECTIONS = [
  {
    icon: Gamepad2,
    color: '#22d3ee',
    title: 'Steer (Joystick)',
    desc: 'WASD keys control movement. The joystick maps to the left analog stick on your phone.',
  },
  {
    icon: Crosshair,
    color: '#f59e0b',
    title: 'Aim (Mouse Look)',
    desc: 'Hold Right Mouse Button to enable mouse camera control. Move your mouse to look around.',
  },
  {
    icon: Target,
    color: '#ef4444',
    title: 'Fire (Shoot)',
    desc: 'Left Mouse Button fires your weapon. Works together with Aim for precise targeting.',
  },
  {
    icon: MousePointerClick,
    color: '#10b981',
    title: 'Tap (Action)',
    desc: 'Single key presses for actions like Jump (Space), Reload (R), Crouch (C), Prone (Z), Interact (F).',
  },
  {
    icon: Move,
    color: '#a855f7',
    title: 'Swipe (Scope)',
    desc: 'Simulates a swipe gesture, used for scoping in/out and drag-based controls.',
  },
];

const DEFAULT_BINDINGS = [
  { key: 'WASD', action: 'Move' },
  { key: 'Right Click', action: 'Aim / Look' },
  { key: 'Left Click', action: 'Fire' },
  { key: 'Space', action: 'Jump' },
  { key: 'C', action: 'Crouch' },
  { key: 'Z', action: 'Prone' },
  { key: 'R', action: 'Reload' },
  { key: 'F', action: 'Interact / Pick up' },
  { key: 'Q / E', action: 'Lean Left / Right' },
  { key: 'Shift', action: 'Sprint' },
  { key: '1 / 2 / 3', action: 'Switch Weapons' },
  { key: '4 / 5', action: 'Grenades / Smoke' },
  { key: 'M', action: 'Map' },
  { key: 'V', action: 'Scope' },
  { key: 'Ctrl+H', action: 'Toggle key overlay' },
];

export function HelpModal({ open, onClose }: HelpModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Keyboard size={20} className="text-cyan-400" /> How to Play PUBG Mobile
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto gm-scroll p-5 space-y-5">
          {/* Key Types */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Key Types</h3>
            <div className="grid grid-cols-1 gap-2.5">
              {HELP_SECTIONS.map(s => {
                const Icon = s.icon;
                return (
                  <div key={s.title} className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/50">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: `${s.color}22`, border: `1px solid ${s.color}55` }}
                    >
                      <Icon size={18} style={{ color: s.color }} />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-white">{s.title}</h4>
                      <p className="text-xs text-slate-400 mt-0.5">{s.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Default Bindings */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Default PUBG Bindings</h3>
            <div className="grid grid-cols-2 gap-2">
              {DEFAULT_BINDINGS.map(b => (
                <div key={b.key} className="flex items-center gap-2.5 p-2 rounded-md bg-slate-800/50">
                  <kbd className="text-[10px] font-mono font-bold text-cyan-400 bg-cyan-500/10 border border-cyan-600/30 rounded px-1.5 py-0.5 min-w-[70px] text-center">
                    {b.key}
                  </kbd>
                  <span className="text-xs text-slate-300">{b.action}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-600/30">
            <h3 className="text-sm font-bold text-amber-400 mb-2">Tips</h3>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
              <li>Click <strong>Edit Keymap</strong> to drag keys to match your phone's on-screen buttons</li>
              <li>Right-click any key in edit mode to delete it</li>
              <li>Adjust Aim Sensitivity separately for scoped vs hip-fire aiming</li>
              <li>Save custom profiles for different games or layouts</li>
              <li>Use Ctrl+H to quickly toggle the key overlay during gameplay</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
