import { Play, Square, HelpCircle, Activity, Cpu, Wifi } from 'lucide-react';

interface BottomBarProps {
  connected: boolean;
  streaming: boolean;
  fps: number;
  latency: number;
  onToggleStream: () => void;
  onHelp: () => void;
}

export function BottomBar({
  connected,
  streaming,
  fps,
  latency,
  onToggleStream,
  onHelp,
}: BottomBarProps) {
  return (
    <div className="h-14 bg-slate-950 border-t border-slate-800 flex items-center justify-between px-4">
      {/* Left: Start/Stop */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleStream}
          disabled={!connected}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed ${
            streaming
              ? 'bg-red-500 text-white hover:bg-red-400 shadow-lg shadow-red-500/30'
              : 'bg-cyan-500 text-white hover:bg-cyan-400 shadow-lg shadow-cyan-500/30'
          }`}
        >
          {streaming ? <Square size={16} /> : <Play size={16} />}
          {streaming ? 'Stop' : 'Start'}
        </button>
        {!connected && (
          <span className="text-[10px] text-slate-500">Connect a device to start streaming</span>
        )}
      </div>

      {/* Center: Stats */}
      {streaming && (
        <div className="flex items-center gap-5">
          <div className="flex items-center gap-1.5">
            <Activity size={14} className={fps > 50 ? 'text-emerald-400' : fps > 25 ? 'text-amber-400' : 'text-red-400'} />
            <span className="text-xs font-mono text-slate-300">
              <span className="text-slate-500">FPS</span> <span className="font-bold tabular-nums">{fps}</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Cpu size={14} className="text-cyan-400" />
            <span className="text-xs font-mono text-slate-300">
              <span className="text-slate-500">Latency</span> <span className="font-bold tabular-nums">{latency}ms</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Wifi size={14} className="text-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-emerald-400 font-bold">Streaming</span>
          </div>
        </div>
      )}

      {/* Right: Help */}
      <button
        onClick={onHelp}
        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
      >
        <HelpCircle size={15} /> How to Play PUBG
      </button>
    </div>
  );
}
