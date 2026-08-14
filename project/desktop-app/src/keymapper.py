"""
Keymapper - maps keyboard/mouse inputs to touch events on the device screen.
Uses pynput for global keyboard/mouse hooking and ScrcpyCore for touch injection.

Key Types:
  - steer: WASD joystick (analog movement via multi-touch)
  - aim: right mouse button hold + mouse move = camera look
  - fire: left mouse button = tap fire button
  - tap: single key tap = tap at screen position
  - swipe: key press = swipe gesture at position
"""
import os
import json
import math
import time
import threading

from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal


class KeyBinding:
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.type = data.get("type", "tap")
        self.key = data.get("key", "")
        self.label = data.get("label", "")
        self.x = data.get("x", 50)  # percentage 0-100
        self.y = data.get("y", 50)
        self.size = data.get("size", 60)
        self.swipe_distance = data.get("swipeDistance", 100)
        self.swipe_angle = data.get("swipeAngle", 0)


class KeymapProfile:
    def __init__(self, data: dict):
        self.name = data.get("name", "Custom")
        self.sensitivity = data.get("sensitivity", 8)
        self.aim_sensitivity = data.get("aimSensitivity", 6)
        self.keys = [KeyBinding(k) for k in data.get("keys", [])]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "sensitivity": self.sensitivity,
            "aimSensitivity": self.aim_sensitivity,
            "keys": [{
                "id": k.id, "type": k.type, "key": k.key,
                "label": k.label, "x": k.x, "y": k.y,
                "size": k.size, "swipeDistance": k.swipe_distance,
                "swipeAngle": k.swipe_angle,
            } for k in self.keys],
        }


class Keymapper(QObject):
    key_activated = Signal(str)  # emits key label for visual feedback

    def __init__(self, scrcpy_core):
        super().__init__()
        self.scrcpy = scrcpy_core
        self.profile = None
        self.enabled = False
        self.screen_w = 1080
        self.screen_h = 2400
        self.mouse_sensitivity = 8
        self.aim_sensitivity = 6

        self._active_touches = {}  # pointer_id -> key_id
        self._steer_active = False
        self._steer_keys = set()
        self._steer_center = (0, 0)
        self._steer_pointer_id = 1000
        self._aim_active = False
        self._fire_active = False
        self._prev_mouse_pos = (0, 0)

        self._kb_listener = None
        self._mouse_listener = None
        self._lock = threading.Lock()

    def set_profile(self, profile: KeymapProfile):
        self.profile = profile

    def set_screen_size(self, w: int, h: int):
        self.screen_w = w
        self.screen_h = h

    def set_enabled(self, enabled: bool):
        if enabled and not self.enabled:
            self.enabled = True
            self._start_listeners()
        elif not enabled and self.enabled:
            self.enabled = False
            self._stop_listeners()
            self._release_all()

    def _start_listeners(self):
        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._kb_listener.daemon = True
        self._kb_listener.start()

        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

    def _stop_listeners(self):
        if self._kb_listener:
            self._kb_listener.stop()
            self._kb_listener = None
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _release_all(self):
        with self._lock:
            for pid in list(self._active_touches.keys()):
                self.scrcpy.inject_touch(self.scrcpy.ACTION_UP,
                                         0, 0, pointer_id=pid, pressure=0)
            self._active_touches.clear()
            self._steer_active = False
            self._steer_keys.clear()
            self._aim_active = False
            self._fire_active = False

    def _pct_to_px(self, x_pct: float, y_pct: float) -> tuple:
        x = int(x_pct / 100.0 * self.screen_w)
        y = int(y_pct / 100.0 * self.screen_h)
        return x, y

    def _find_keys_by_key(self, key_str: str) -> list:
        if not self.profile:
            return []
        return [k for k in self.profile.keys if k.key.upper() == key_str.upper()]

    def _find_key_by_type(self, key_type: str) -> 'KeyBinding':
        if not self.profile:
            return None
        for k in self.profile.keys:
            if k.type == key_type:
                return k
        return None

    def _key_to_str(self, key) -> str:
        if hasattr(key, 'char') and key.char:
            return key.char.upper()
        if hasattr(key, 'name'):
            name = key.name.upper()
            if name == 'SPACE':
                return 'SPACE'
            if name == 'SHIFT':
                return 'SHIFT'
            if name == 'CTRL':
                return 'CTRL'
            if name == 'TAB':
                return 'TAB'
            if name == 'ENTER':
                return 'ENTER'
            return name
        return str(key).upper()

    def _on_key_press(self, key):
        if not self.enabled or not self.profile:
            return

        key_str = self._key_to_str(key)
        steer_key = self._find_key_by_type("steer")
        steer_keys_set = set()
        if steer_key:
            for c in steer_key.key.upper():
                steer_keys_set.add(c)

        with self._lock:
            # Handle steering (WASD)
            if key_str in steer_keys_set and steer_key:
                self._steer_keys.add(key_str)
                self._update_steer(steer_key)
                return

            # Handle tap keys
            tap_keys = [k for k in self._find_keys_by_key(key_str) if k.type == "tap"]
            for tk in tap_keys:
                self._do_tap(tk)

            # Handle swipe keys
            swipe_keys = [k for k in self._find_keys_by_key(key_str) if k.type == "swipe"]
            for sk in swipe_keys:
                self._do_swipe(sk)

    def _on_key_release(self, key):
        if not self.enabled or not self.profile:
            return

        key_str = self._key_to_str(key)
        steer_key = self._find_key_by_type("steer")
        steer_keys_set = set()
        if steer_key:
            for c in steer_key.key.upper():
                steer_keys_set.add(c)

        with self._lock:
            if key_str in steer_keys_set:
                self._steer_keys.discard(key_str)
                self._update_steer(steer_key)

    def _update_steer(self, steer_key: KeyBinding):
        """Update joystick position based on currently pressed WASD keys."""
        cx, cy = self._pct_to_px(steer_key.x, steer_key.y)
        radius = int(steer_key.size * self.screen_w / 100 * 0.4)

        dx = 0
        dy = 0
        if 'W' in self._steer_keys:
            dy -= 1
        if 'S' in self._steer_keys:
            dy += 1
        if 'A' in self._steer_keys:
            dx -= 1
        if 'D' in self._steer_keys:
            dx += 1

        if dx == 0 and dy == 0:
            # Release joystick
            if self._steer_active:
                self.scrcpy.inject_touch(self.scrcpy.ACTION_UP,
                                         cx, cy, pointer_id=self._steer_pointer_id,
                                         pressure=0)
                self._steer_active = False
                if self._steer_pointer_id in self._active_touches:
                    del self._active_touches[self._steer_pointer_id]
        else:
            # Normalize diagonal
            mag = math.sqrt(dx * dx + dy * dy)
            if mag > 0:
                dx = dx / mag
                dy = dy / mag
            tx = int(cx + dx * radius)
            ty = int(cy + dy * radius)

            if not self._steer_active:
                self.scrcpy.inject_touch(self.scrcpy.ACTION_DOWN,
                                         cx, cy, pointer_id=self._steer_pointer_id,
                                         pressure=1.0)
                self._steer_active = True
                self._active_touches[self._steer_pointer_id] = "steer"

            self.scrcpy.inject_touch(self.scrcpy.ACTION_MOVE,
                                     tx, ty, pointer_id=self._steer_pointer_id,
                                     pressure=1.0)

    def _do_tap(self, binding: KeyBinding):
        """Quick tap at the key position."""
        x, y = self._pct_to_px(binding.x, binding.y)
        pid = hash(binding.id) & 0xFFFFFFFF
        self.scrcpy.inject_touch(self.scrcpy.ACTION_DOWN, x, y,
                                 pointer_id=pid, pressure=1.0)
        time.sleep(0.03)
        self.scrcpy.inject_touch(self.scrcpy.ACTION_UP, x, y,
                                 pointer_id=pid, pressure=0)
        self.key_activated.emit(binding.label)

    def _do_swipe(self, binding: KeyBinding):
        """Swipe gesture from key position."""
        x, y = self._pct_to_px(binding.x, binding.y)
        angle_rad = math.radians(binding.swipe_angle)
        dist = binding.swipe_distance
        end_x = int(x + math.cos(angle_rad) * dist)
        end_y = int(y + math.sin(angle_rad) * dist)
        # Run in thread so it doesn't block
        t = threading.Thread(
            target=self.scrcpy.inject_swipe,
            args=(x, y, end_x, end_y, 300),
            daemon=True
        )
        t.start()
        self.key_activated.emit(binding.label)

    def _on_mouse_click(self, x, y, button, pressed):
        if not self.enabled or not self.profile:
            return

        with self._lock:
            if button == mouse.Button.left:
                fire_key = self._find_key_by_type("fire")
                if fire_key and pressed:
                    fx, fy = self._pct_to_px(fire_key.x, fire_key.y)
                    pid = 2000
                    self.scrcpy.inject_touch(self.scrcpy.ACTION_DOWN, fx, fy,
                                             pointer_id=pid, pressure=1.0)
                    self._fire_active = True
                    self._active_touches[pid] = "fire"
                    self.key_activated.emit("Fire")
                elif fire_key and not pressed and self._fire_active:
                    fx, fy = self._pct_to_px(fire_key.x, fire_key.y)
                    self.scrcpy.inject_touch(self.scrcpy.ACTION_UP, fx, fy,
                                             pointer_id=2000, pressure=0)
                    self._fire_active = False
                    if 2000 in self._active_touches:
                        del self._active_touches[2000]

            elif button == mouse.Button.right:
                if pressed:
                    self._aim_active = True
                    self._prev_mouse_pos = (x, y)
                    self.key_activated.emit("Aim")
                else:
                    self._aim_active = False

    def _on_mouse_move(self, x, y):
        if not self.enabled or not self._aim_active or not self.profile:
            return

        with self._lock:
            dx = x - self._prev_mouse_pos[0]
            dy = y - self._prev_mouse_pos[1]
            self._prev_mouse_pos = (x, y)

            # Scale by sensitivity
            sens = self.aim_sensitivity / 10.0
            aim_key = self._find_key_by_type("aim")
            if not aim_key:
                return

            # Move the camera by injecting touch move at aim position
            ax, ay = self._pct_to_px(aim_key.x, aim_key.y)
            # Start touch if not yet started
            if 3000 not in self._active_touches:
                self.scrcpy.inject_touch(self.scrcpy.ACTION_DOWN, ax, ay,
                                         pointer_id=3000, pressure=1.0)
                self._active_touches[3000] = "aim"

            new_x = int(max(0, min(self.screen_w, ax + dx * sens * 5)))
            new_y = int(max(0, min(self.screen_h, ay + dy * sens * 5)))
            self.scrcpy.inject_touch(self.scrcpy.ACTION_MOVE, new_x, new_y,
                                     pointer_id=3000, pressure=1.0)

    def load_from_file(self, filepath: str) -> KeymapProfile:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.profile = KeymapProfile(data)
            return self.profile
        except Exception as e:
            print(f"[Keymapper] Load error: {e}")
            return None

    def save_to_file(self, filepath: str, profile: KeymapProfile):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[Keymapper] Save error: {e}")
