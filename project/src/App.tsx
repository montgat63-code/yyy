import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Gamepad2, Radio, Maximize2, Eye, EyeOff,
} from 'lucide-react';
import type { KeyType, DeviceSettings, KeymapProfile } from '@/types';
import {
  PUBG_MOBILE_PRESET, BUILT_IN_PRESETS, createKey,
} from '@/presets';
import { useLocalStorage } from '@/hooks/useLocalStorage';
import { LeftPanel } from '@/components/LeftPanel';
import { RightPanel } from '@/components/RightPanel';
import { BottomBar } from '@/components/BottomBar';
import { KeyOverlay } from '@/components/KeyOverlay';
import { HelpModal } from '@/components/HelpModal';

const DEFAULT_SETTINGS: DeviceSettings = {
  resolution: 1080,
  fps: 60,
  bitrate: 8,
  lowLatency: true,
  showKeys: true,
  keyOpacity: 70,
  keySize: 100,
  mouseSensitivity: 8,
  aimSensitivity: 6,
};

const BG_IMAGE = 'https://images.pexels.com/photos/669277/pexels-photo-669277.jpeg?auto=compress&cs=tinysrgb&h=650&w=940';

export default function App() {
  const [settings, setSettings] = useLocalStorage<DeviceSettings>('gm_settings', DEFAULT_SETTINGS);
  const [currentProfile, setCurrentProfile] = useLocalStorage<KeymapProfile>('gm_current_profile', PUBG_MOBILE_PRESET);
  const [savedProfiles, setSavedProfiles] = useLocalStorage<KeymapProfile[]>('gm_saved_profiles', BUILT_IN_PRESETS);

  const [editMode, setEditMode] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(true);
  const [deviceName] = useState('Samsung Galaxy S24 Ultra');
  const [fps, setFps] = useState(60);
  const [latency, setLatency] = useState(15);
  const [helpOpen, setHelpOpen] = useState(false);

  const keys = currentProfile.keys;
  const videoAreaRef = useRef<HTMLDivElement>(null);

  // Simulated FPS/latency counter when streaming
  useEffect(() => {
    if (!streaming) return;
    const interval = setInterval(() => {
      const target = settings.fps;
      const jitter = Math.floor(Math.random() * 5) - 2;
      setFps(Math.max(20, Math.min(target, target + jitter)));
      setLatency(settings.lowLatency
        ? 10 + Math.floor(Math.random() * 8)
        : 25 + Math.floor(Math.random() * 15));
    }, 800);
    return () => clearInterval(interval);
  }, [streaming, settings.fps, settings.lowLatency]);

  // Ctrl+H to toggle key overlay
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key.toLowerCase() === 'h') {
        e.preventDefault();
        setSettings(s => ({ ...s, showKeys: !s.showKeys }));
      }
      if (e.key === 'Escape' && editMode) {
        setEditMode(false);
        setSelectedId(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [editMode, setSettings]);

  const updateSettings = useCallback((patch: Partial<DeviceSettings>) => {
    setSettings(s => ({ ...s, ...patch }));
  }, [setSettings]);

  const handleAddKey = useCallback((type: KeyType) => {
    const defaults: Record<KeyType, { key: string; label: string }> = {
      steer: { key: 'WASD', label: 'Move' },
      aim: { key: 'RMB', label: 'Aim' },
      fire: { key: 'LMB', label: 'Fire' },
      tap: { key: 'F', label: 'Action' },
      swipe: { key: 'V', label: 'Swipe' },
    };
    const d = defaults[type];
    const newKey = createKey(type, d.key, d.label, 50, 50, 50);
    setCurrentProfile(p => ({ ...p, keys: [...p.keys, newKey] }));
    setSelectedId(newKey.id);
  }, [setCurrentProfile]);

  const handleDragKey = useCallback((id: string, xPct: number, yPct: number) => {
    setCurrentProfile(p => ({
      ...p,
      keys: p.keys.map(k => k.id === id ? { ...k, x: xPct, y: yPct } : k),
    }));
  }, [setCurrentProfile]);

  const handleDeleteKey = useCallback((id: string) => {
    setCurrentProfile(p => ({ ...p, keys: p.keys.filter(k => k.id !== id) }));
    setSelectedId(prev => prev === id ? null : prev);
  }, [setCurrentProfile]);

  const handleRenameKey = useCallback((id: string, key: string) => {
    setCurrentProfile(p => ({
      ...p,
      keys: p.keys.map(k => k.id === id ? { ...k, key } : k),
    }));
  }, [setCurrentProfile]);

  const handleRenameLabel = useCallback((id: string, label: string) => {
    setCurrentProfile(p => ({
      ...p,
      keys: p.keys.map(k => k.id === id ? { ...k, label } : k),
    }));
  }, [setCurrentProfile]);

  const handleSaveProfile = useCallback(() => {
    const name = currentProfile.name;
    setSavedProfiles(prev => {
      const exists = prev.some(p => p.name === name);
      if (exists) {
        return prev.map(p => p.name === name ? currentProfile : p);
      }
      return [...prev, currentProfile];
    });
  }, [currentProfile, setSavedProfiles]);

  const handleLoadProfile = useCallback((name: string) => {
    const profile = savedProfiles.find(p => p.name === name);
    if (profile) {
      setCurrentProfile({ ...profile, keys: profile.keys.map(k => ({ ...k, id: k.id })) });
      setSelectedId(null);
    }
  }, [savedProfiles, setCurrentProfile]);

  const handleNewProfile = useCallback(() => {
    const name = `Custom Profile ${Date.now() % 10000}`;
    setCurrentProfile({
      name,
      sensitivity: settings.mouseSensitivity,
      aimSensitivity: settings.aimSensitivity,
      keys: [],
    });
    setSelectedId(null);
    setEditMode(true);
  }, [setCurrentProfile, settings]);

  const handleExportProfile = useCallback(() => {
    const json = JSON.stringify(currentProfile, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentProfile.name.replace(/\s+/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [currentProfile]);

  const handleReconnect = useCallback(() => {
    setConnected(true);
  }, []);

  const handleToggleStream = useCallback(() => {
    setStreaming(s => !s);
  }, []);

  const sizeScale = settings.keySize / 100;

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 overflow-hidden select-none">
      {/* Top Bar */}
      <header className="h-12 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
            <Gamepad2 size={18} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-tight">GameMaster</h1>
            <p className="text-[9px] text-slate-500 leading-tight">PUBG Controller</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs">
            <Radio size={13} className={connected ? 'text-emerald-400 animate-pulse' : 'text-slate-600'} />
            <span className={connected ? 'text-emerald-400 font-medium' : 'text-slate-600'}>
              {connected ? 'ADB Connected' : 'Disconnected'}
            </span>
          </div>
          <button
            onClick={() => updateSettings({ showKeys: !settings.showKeys })}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            {settings.showKeys ? <Eye size={14} /> : <EyeOff size={14} />}
            {settings.showKeys ? 'Keys Visible' : 'Keys Hidden'}
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        <LeftPanel
          settings={settings}
          onSettingsChange={updateSettings}
          connected={connected}
          deviceName={deviceName}
          onReconnect={handleReconnect}
        />

        {/* Center: Video Display */}
        <div className="flex-1 relative bg-black overflow-hidden">
          {/* Video area */}
          <div ref={videoAreaRef} className="absolute inset-0">
            {/* Simulated device screen */}
            {streaming ? (
              <div className="absolute inset-0">
                <img
                  src={BG_IMAGE}
                  alt="Device screen"
                  className="w-full h-full object-cover"
                  style={{ filter: 'saturate(1.1) contrast(1.05)' }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-black/20" />
                {/* HUD simulation */}
                <div className="absolute top-3 left-3 text-[10px] text-white/60 font-mono">
                  Erangel - Squad TPP
                </div>
                <div className="absolute top-3 right-3 text-[10px] text-white/60 font-mono flex items-center gap-2">
                  <span className="text-emerald-400">42</span> Alive
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="w-20 h-20 rounded-2xl bg-slate-800/50 border border-slate-700 flex items-center justify-center mb-4">
                  <Gamepad2 size={36} className="text-slate-600" />
                </div>
                <p className="text-sm font-semibold text-slate-400">No Stream Active</p>
                <p className="text-xs text-slate-600 mt-1">Press Start to begin mirroring your device</p>
                <div className="mt-6 flex items-center gap-3 text-[10px] text-slate-600">
                  <span className="flex items-center gap-1"><Maximize2 size={10} /> {settings.resolution}p</span>
                  <span>|</span>
                  <span>{settings.fps} FPS</span>
                  <span>|</span>
                  <span>{settings.bitrate} Mbps</span>
                </div>
              </div>
            )}

            {/* Key Overlay */}
            {settings.showKeys && (
              <KeyOverlay
                keys={keys}
                opacity={settings.keyOpacity}
                sizeScale={sizeScale}
                editMode={editMode}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onDelete={handleDeleteKey}
                onDrag={handleDragKey}
              />
            )}

            {/* Edit mode grid */}
            {editMode && (
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(34,211,238,0.07) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(34,211,238,0.07) 1px, transparent 1px)
                  `,
                  backgroundSize: '40px 40px',
                }}
              />
            )}

            {/* Edit mode banner */}
            {editMode && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-amber-500/90 text-white text-xs font-bold shadow-lg z-30">
                Edit Mode - Drag keys, right-click to delete, Esc to exit
              </div>
            )}
          </div>
        </div>

        <RightPanel
          keys={keys}
          profiles={savedProfiles}
          currentProfileName={currentProfile.name}
          editMode={editMode}
          selectedId={selectedId}
          onToggleEditMode={() => { setEditMode(e => !e); setSelectedId(null); }}
          onAddKey={handleAddKey}
          onSelectKey={setSelectedId}
          onDeleteKey={handleDeleteKey}
          onRenameKey={handleRenameKey}
          onRenameLabel={handleRenameLabel}
          onSaveProfile={handleSaveProfile}
          onLoadProfile={handleLoadProfile}
          onExportProfile={handleExportProfile}
          onNewProfile={handleNewProfile}
        />
      </div>

      <BottomBar
        connected={connected}
        streaming={streaming}
        fps={fps}
        latency={latency}
        onToggleStream={handleToggleStream}
        onHelp={() => setHelpOpen(true)}
      />

      <HelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
}
