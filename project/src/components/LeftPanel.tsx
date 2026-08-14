import {
  Smartphone, Monitor, RefreshCw, Zap, Gauge, Eye, MousePointer,
  Crosshair, Settings, Wifi,
} from 'lucide-react';
import type { DeviceSettings } from '@/types';
import { Slider } from './Slider';
import { Toggle } from './Toggle';

interface LeftPanelProps {
  settings: DeviceSettings;
  onSettingsChange: (patch: Partial<DeviceSettings>) => void;
  connected: boolean;
  deviceName: string;
  onReconnect: () => void;
}

export function LeftPanel({
  settings,
  onSettingsChange,
  connected,
  deviceName,
  onReconnect,
}: LeftPanelProps) {
  return (
    <div className="w-64 bg-slate-900/80 border-r border-slate-800 flex flex-col overflow-y-auto gm-scroll">
      {/* Device Section */}
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
          <Smartphone size={14} /> Device
        </h3>
        <div className={`p-3 rounded-lg border ${connected ? 'bg-emerald-500/10 border-emerald-600/40' : 'bg-slate-800 border-slate-700'}`}>
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            <span className="text-sm font-semibold text-white truncate">{connected ? deviceName : 'No device'}</span>
          </div>
          <p className="text-[10px] text-slate-400 mb-2">
            {connected ? 'USB connection active' : 'Connect via USB / ADB'}
          </p>
          <button
            onClick={onReconnect}
            className="w-full flex items-center justify-center gap-1.5 text-xs font-medium text-cyan-400 hover:text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 rounded-md py-1.5 transition-colors"
          >
            <Wifi size={13} /> {connected ? 'Reconnect' : 'Connect'}
          </button>
        </div>
      </div>

      {/* Video Section */}
      <div className="p-4 border-b border-slate-800 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-2">
          <Monitor size={14} /> Video
        </h3>

        <div className="space-y-1.5">
          <span className="text-xs font-medium text-slate-400">Resolution</span>
          <div className="grid grid-cols-2 gap-2">
            {[720, 1080].map(r => (
              <button
                key={r}
                onClick={() => onSettingsChange({ resolution: r as 720 | 1080 })}
                className={`text-xs font-semibold py-1.5 rounded-md transition-all ${
                  settings.resolution === r
                    ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {r}p
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-1.5">
          <span className="text-xs font-medium text-slate-400">Frame Rate</span>
          <div className="grid grid-cols-2 gap-2">
            {[30, 60].map(f => (
              <button
                key={f}
                onClick={() => onSettingsChange({ fps: f as 30 | 60 })}
                className={`text-xs font-semibold py-1.5 rounded-md transition-all flex items-center justify-center gap-1 ${
                  settings.fps === f
                    ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                <RefreshCw size={11} /> {f} FPS
              </button>
            ))}
          </div>
        </div>

        <Slider
          label="Bitrate"
          value={settings.bitrate}
          min={2}
          max={20}
          step={1}
          unit=" Mbps"
          onChange={v => onSettingsChange({ bitrate: v })}
        />

        <Toggle
          label="Low Latency"
          checked={settings.lowLatency}
          onChange={v => onSettingsChange({ lowLatency: v })}
          hint="Reduce buffer for faster response"
        />
      </div>

      {/* Overlay Section */}
      <div className="p-4 border-b border-slate-800 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-2">
          <Eye size={14} /> Overlay
        </h3>

        <Toggle
          label="Show Keys"
          checked={settings.showKeys}
          onChange={v => onSettingsChange({ showKeys: v })}
          hint="Toggle with Ctrl+H"
        />

        <Slider
          label="Key Opacity"
          value={settings.keyOpacity}
          min={20}
          max={100}
          step={5}
          unit="%"
          onChange={v => onSettingsChange({ keyOpacity: v })}
        />

        <Slider
          label="Key Size"
          value={settings.keySize}
          min={50}
          max={150}
          step={5}
          unit="%"
          onChange={v => onSettingsChange({ keySize: v })}
        />
      </div>

      {/* Sensitivity Section */}
      <div className="p-4 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1 flex items-center gap-2">
          <Gauge size={14} /> Sensitivity
        </h3>

        <Slider
          label="Mouse Sensitivity"
          value={settings.mouseSensitivity}
          min={1}
          max={20}
          onChange={v => onSettingsChange({ mouseSensitivity: v })}
        />

        <Slider
          label="Aim Sensitivity"
          value={settings.aimSensitivity}
          min={1}
          max={20}
          onChange={v => onSettingsChange({ aimSensitivity: v })}
          />

        <div className="pt-1 flex items-start gap-2 text-[10px] text-slate-500">
          <Settings size={12} className="mt-0.5 flex-shrink-0" />
          <span>Higher = faster camera movement. Adjust per weapon scope.</span>
        </div>
      </div>

      {/* Decorative status row */}
      <div className="mt-auto p-3 border-t border-slate-800 bg-slate-950/50">
        <div className="flex items-center justify-between text-[10px] text-slate-500">
          <span className="flex items-center gap-1"><Zap size={10} className="text-cyan-500" /> Scrcpy Engine</span>
          <span className="flex items-center gap-1"><Crosshair size={10} className="text-cyan-500" /> {settings.resolution}p@{settings.fps}</span>
        </div>
      </div>
    </div>
  );
}
