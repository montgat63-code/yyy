export type KeyType = 'steer' | 'aim' | 'fire' | 'tap' | 'swipe';

export interface KeyBinding {
  id: string;
  type: KeyType;
  key: string;
  label: string;
  x: number;
  y: number;
  size: number;
  swipeAngle?: number;
  swipeDistance?: number;
  swipeKey?: string;
}

export interface KeymapProfile {
  name: string;
  sensitivity: number;
  aimSensitivity: number;
  keys: KeyBinding[];
}

export interface DeviceSettings {
  resolution: 720 | 1080;
  fps: 30 | 60;
  bitrate: number;
  lowLatency: boolean;
  showKeys: boolean;
  keyOpacity: number;
  keySize: number;
  mouseSensitivity: number;
  aimSensitivity: number;
}

export const KEY_TYPE_LABELS: Record<KeyType, string> = {
  steer: 'Steer (Joystick)',
  aim: 'Aim (Mouse Look)',
  fire: 'Fire (Shoot)',
  tap: 'Tap (Action)',
  swipe: 'Swipe (Scope)',
};

export const KEY_TYPE_COLORS: Record<KeyType, string> = {
  steer: '#22d3ee',
  aim: '#f59e0b',
  fire: '#ef4444',
  tap: '#10b981',
  swipe: '#a855f7',
};

export const KEY_TYPE_ICONS: Record<KeyType, string> = {
  steer: 'Gamepad2',
  aim: 'Crosshair',
  fire: 'Target',
  tap: 'MousePointerClick',
  swipe: 'Move',
};
