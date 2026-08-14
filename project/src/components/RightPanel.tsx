import {
  Plus, Save, FolderOpen, Trash2, Edit3, List, Gamepad2,
  Crosshair, Target, MousePointerClick, Move, FileDown,
  type LucideIcon,
} from 'lucide-react';
import type { KeyType, KeyBinding, KeymapProfile } from '@/types';
import { KEY_TYPE_LABELS, KEY_TYPE_COLORS } from '@/types';

const TYPE_ICONS: Record<KeyType, LucideIcon> = {
  steer: Gamepad2,
  aim: Crosshair,
  fire: Target,
  tap: MousePointerClick,
  swipe: Move,
};

interface RightPanelProps {
  keys: KeyBinding[];
  profiles: KeymapProfile[];
  currentProfileName: string;
  editMode: boolean;
  selectedId: string | null;
  onToggleEditMode: () => void;
  onAddKey: (type: KeyType) => void;
  onSelectKey: (id: string | null) => void;
  onDeleteKey: (id: string) => void;
  onRenameKey: (id: string, key: string) => void;
  onRenameLabel: (id: string, label: string) => void;
  onSaveProfile: () => void;
  onLoadProfile: (name: string) => void;
  onExportProfile: () => void;
  onNewProfile: () => void;
}

export function RightPanel({
  keys,
  profiles,
  currentProfileName,
  editMode,
  selectedId,
  onToggleEditMode,
  onAddKey,
  onSelectKey,
  onDeleteKey,
  onRenameKey,
  onRenameLabel,
  onSaveProfile,
  onLoadProfile,
  onExportProfile,
  onNewProfile,
}: RightPanelProps) {
  const selectedKey = keys.find(k => k.id === selectedId);

  return (
    <div className="w-72 bg-slate-900/80 border-l border-slate-800 flex flex-col overflow-hidden">
      {/* Edit Mode Toggle */}
      <div className="p-4 border-b border-slate-800">
        <button
          onClick={onToggleEditMode}
          className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-semibold text-sm transition-all ${
            editMode
              ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/30'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          }`}
        >
          <Edit3 size={16} /> {editMode ? 'Exit Edit Mode' : 'Edit Keymap'}
        </button>
        {editMode && (
          <p className="text-[10px] text-amber-400/80 mt-2 text-center">
            Drag keys to position - Right-click to delete
          </p>
        )}
      </div>

      {/* Add Key Panel */}
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
          <Plus size={14} /> Add New Key
        </h3>
        <div className="space-y-1.5">
          {(Object.keys(KEY_TYPE_LABELS) as KeyType[]).map(type => {
            const Icon = TYPE_ICONS[type];
            const color = KEY_TYPE_COLORS[type];
            return (
              <button
                key={type}
                onClick={() => onAddKey(type)}
                disabled={!editMode}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors group"
              >
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${color}22`, border: `1px solid ${color}55` }}
                >
                  <Icon size={15} style={{ color }} />
                </div>
                <span className="text-xs font-medium text-slate-300 group-hover:text-white">
                  {KEY_TYPE_LABELS[type]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Key Editor */}
      {editMode && selectedKey && (
        <div className="p-4 border-b border-slate-800 bg-slate-800/30">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
            Edit Selected Key
          </h3>
          <div className="space-y-3">
            <div>
              <label className="text-[10px] text-slate-500 block mb-1">Label</label>
              <input
                type="text"
                value={selectedKey.label}
                onChange={e => {
                  const k = keys.find(kk => kk.id === selectedKey.id);
                  if (k) onRenameLabel(k.id, e.target.value);
                }}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1.5 text-xs text-white focus:border-cyan-500 outline-none"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-500 block mb-1">Assigned Key</label>
              <input
                type="text"
                value={selectedKey.key}
                onChange={e => onRenameKey(selectedKey.id, e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-2 py-1.5 text-xs text-white focus:border-cyan-500 outline-none uppercase"
              />
            </div>
            <button
              onClick={() => onDeleteKey(selectedKey.id)}
              className="w-full flex items-center justify-center gap-1.5 text-xs font-medium text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 rounded-md py-1.5 transition-colors"
            >
              <Trash2 size={13} /> Delete Key
            </button>
          </div>
        </div>
      )}

      {/* Key List */}
      <div className="flex-1 overflow-y-auto gm-scroll p-4 border-b border-slate-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
          <List size={14} /> Keys ({keys.length})
        </h3>
        <div className="space-y-1">
          {keys.map(k => {
            const Icon = TYPE_ICONS[k.type];
            const color = KEY_TYPE_COLORS[k.type];
            return (
              <div
                key={k.id}
                onClick={() => editMode && onSelectKey(k.id)}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md cursor-pointer transition-colors ${
                  selectedId === k.id ? 'bg-slate-700' : 'hover:bg-slate-800'
                }`}
              >
                <Icon size={13} style={{ color }} />
                <span className="text-xs font-mono font-bold w-12 text-slate-300">{k.key}</span>
                <span className="text-[10px] text-slate-500 truncate flex-1">{k.label}</span>
              </div>
            );
          })}
          {keys.length === 0 && (
            <p className="text-[10px] text-slate-600 text-center py-4">No keys added yet</p>
          )}
        </div>
      </div>

      {/* Profile Management */}
      <div className="p-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
          Profiles
        </h3>
        <div className="text-xs font-semibold text-cyan-400 mb-3 truncate">
          {currentProfileName}
        </div>

        <div className="max-h-28 overflow-y-auto gm-scroll mb-3 space-y-1">
          {profiles.map(p => (
            <div
              key={p.name}
              className={`flex items-center justify-between px-2.5 py-1.5 rounded-md cursor-pointer transition-colors ${
                p.name === currentProfileName ? 'bg-cyan-500/15 border border-cyan-600/30' : 'hover:bg-slate-800'
              }`}
              onClick={() => onLoadProfile(p.name)}
            >
              <span className="text-xs text-slate-300 truncate">{p.name}</span>
              <span className="text-[9px] text-slate-500 flex-shrink-0">{p.keys.length} keys</span>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onSaveProfile}
            className="flex items-center justify-center gap-1.5 text-xs font-medium text-white bg-cyan-500 hover:bg-cyan-400 rounded-md py-2 transition-colors"
          >
            <Save size={13} /> Save
          </button>
          <button
            onClick={onNewProfile}
            className="flex items-center justify-center gap-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-md py-2 transition-colors"
          >
            <FolderOpen size={13} /> New
          </button>
        </div>
        <button
          onClick={onExportProfile}
          className="w-full mt-2 flex items-center justify-center gap-1.5 text-[10px] font-medium text-slate-400 hover:text-slate-300 bg-slate-800/50 hover:bg-slate-700/50 rounded-md py-1.5 transition-colors"
        >
          <FileDown size={11} /> Export as JSON
        </button>
      </div>
    </div>
  );
}
