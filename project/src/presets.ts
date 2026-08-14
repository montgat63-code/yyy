import type { KeymapProfile, KeyBinding, KeyType } from './types';

let idCounter = 0;
export const genId = (): string => `key_${Date.now()}_${idCounter++}`;

export function createKey(
  type: KeyType,
  key: string,
  label: string,
  x: number,
  y: number,
  size: number = 60,
  extra?: Partial<KeyBinding>,
): KeyBinding {
  return {
    id: genId(),
    type,
    key,
    label,
    x,
    y,
    size,
    ...extra,
  };
}

export const PUBG_MOBILE_PRESET: KeymapProfile = {
  name: 'PUBG Mobile',
  sensitivity: 8,
  aimSensitivity: 6,
  keys: [
    createKey('steer', 'WASD', 'Move', 22, 78, 80),
    createKey('aim', 'RMB', 'Aim Look', 50, 50, 70),
    createKey('fire', 'LMB', 'Fire', 78, 82, 55),
    createKey('tap', 'Space', 'Jump', 82, 65, 48),
    createKey('tap', 'C', 'Crouch', 15, 55, 44),
    createKey('tap', 'Z', 'Prone', 15, 40, 44),
    createKey('tap', 'R', 'Reload', 73, 72, 44),
    createKey('tap', 'F', 'Interact', 60, 80, 44),
    createKey('tap', 'Q', 'Lean Left', 38, 45, 40),
    createKey('tap', 'E', 'Lean Right', 62, 45, 40),
    createKey('tap', 'Shift', 'Sprint', 35, 72, 44),
    createKey('tap', '1', 'Weapon 1', 88, 35, 40),
    createKey('tap', '2', 'Weapon 2', 93, 50, 40),
    createKey('tap', '3', 'Weapon 3', 88, 65, 40),
    createKey('tap', '4', 'Grenade', 45, 20, 38),
    createKey('tap', '5', 'Smoke', 52, 20, 38),
    createKey('tap', 'M', 'Map', 95, 12, 40),
    createKey('swipe', 'V', 'Scope', 70, 30, 50, { swipeDistance: 120, swipeAngle: 0 }),
  ],
};

export const CALL_OF_DUTY_PRESET: KeymapProfile = {
  name: 'Call of Duty Mobile',
  sensitivity: 7,
  aimSensitivity: 5,
  keys: [
    createKey('steer', 'WASD', 'Move', 22, 78, 80),
    createKey('aim', 'RMB', 'Aim', 50, 50, 70),
    createKey('fire', 'LMB', 'Fire', 80, 80, 55),
    createKey('tap', 'Space', 'Jump', 85, 60, 46),
    createKey('tap', 'C', 'Slide', 12, 60, 44),
    createKey('tap', 'R', 'Reload', 70, 70, 44),
    createKey('tap', 'F', 'Skill', 60, 82, 44),
    createKey('tap', '1', 'Primary', 90, 35, 40),
    createKey('tap', '2', 'Secondary', 95, 50, 40),
    createKey('tap', '3', 'Lethal', 45, 18, 38),
    createKey('tap', '4', 'Tactical', 55, 18, 38),
    createKey('tap', 'M', 'Map', 96, 12, 38),
  ],
};

export const FREE_FIRE_PRESET: KeymapProfile = {
  name: 'Free Fire',
  sensitivity: 9,
  aimSensitivity: 7,
  keys: [
    createKey('steer', 'WASD', 'Move', 20, 75, 80),
    createKey('aim', 'RMB', 'Aim', 48, 50, 70),
    createKey('fire', 'LMB', 'Fire', 82, 78, 55),
    createKey('tap', 'Space', 'Jump', 88, 55, 44),
    createKey('tap', 'C', 'Crouch', 14, 55, 42),
    createKey('tap', 'R', 'Reload', 72, 68, 42),
    createKey('tap', 'F', 'Gloo Wall', 58, 82, 44),
    createKey('tap', '1', 'Weapon', 92, 38, 38),
    createKey('tap', '2', 'Switch', 96, 52, 38),
    createKey('tap', 'M', 'Map', 95, 12, 38),
  ],
};

export const BUILT_IN_PRESETS: KeymapProfile[] = [
  PUBG_MOBILE_PRESET,
  CALL_OF_DUTY_PRESET,
  FREE_FIRE_PRESET,
];

export const KEY_OPTIONS: string[] = [
  'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P',
  'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L',
  'Z', 'X', 'C', 'V', 'B', 'N', 'M',
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
  'Space', 'Shift', 'Ctrl', 'Tab', 'Enter',
  'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
  'LMB', 'RMB', 'MMB',
  'WASD',
];
