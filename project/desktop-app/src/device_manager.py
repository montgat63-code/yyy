"""
Device Manager - handles ADB device discovery and connection.
Bundled adb.exe is searched in /tools/ first, then system PATH.
"""
import os
import subprocess
import re

class DeviceManager:
    def __init__(self, tools_dir: str = None):
        if tools_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tools_dir = os.path.join(base, "tools")
        self.tools_dir = tools_dir
        self.adb_path = self._find_adb()
        self._start_server()

    def _find_adb(self) -> str:
        candidates = [
            os.path.join(self.tools_dir, "adb.exe"),
            os.path.join(self.tools_dir, "adb"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return "adb"

    def _start_server(self):
        try:
            subprocess.run([self.adb_path, "start-server"],
                           capture_output=True, timeout=10)
        except Exception:
            pass

    def list_devices(self) -> list:
        """Returns list of (serial, state) tuples. state is 'device' or 'unauthorized' etc."""
        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True, text=True, timeout=10
            )
            devices = []
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    devices.append((parts[0], parts[1]))
            return devices
        except Exception as e:
            print(f"[DeviceManager] Error listing devices: {e}")
            return []

    def get_device_name(self, serial: str) -> str:
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "shell", "getprop", "ro.product.model"],
                capture_output=True, text=True, timeout=10
            )
            name = result.stdout.strip()
            if name:
                return name
        except Exception:
            pass
        return serial

    def get_screen_size(self, serial: str) -> tuple:
        """Returns (width, height) of the device screen."""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", serial, "shell", "wm", "size"],
                capture_output=True, text=True, timeout=10
            )
            match = re.search(r"(\d+)x(\d+)", result.stdout)
            if match:
                return int(match.group(1)), int(match.group(2))
        except Exception:
            pass
        return 1080, 2400

    def push_file(self, serial: str, local_path: str, remote_path: str) -> bool:
        try:
            subprocess.run(
                [self.adb_path, "-s", serial, "push", local_path, remote_path],
                capture_output=True, timeout=30
            )
            return True
        except Exception as e:
            print(f"[DeviceManager] Push error: {e}")
            return False

    def shell(self, serial: str, *args) -> str:
        try:
            cmd = [self.adb_path, "-s", serial, "shell"] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            print(f"[DeviceManager] Shell error: {e}")
            return ""

    def forward_port(self, serial: str, local: int, remote: int) -> bool:
        try:
            subprocess.run(
                [self.adb_path, "-s", serial, "forward", f"tcp:{local}", f"tcp:{remote}"],
                capture_output=True, timeout=10
            )
            return True
        except Exception as e:
            print(f"[DeviceManager] Forward error: {e}")
            return False
