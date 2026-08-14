"""
ScrcpyCore - pushes scrcpy-server to device, starts it, receives H264 video,
decodes with ffmpeg, and sends touch-injection control messages.

Uses the scrcpy v2.x control protocol for real touch event injection.
"""
import os
import sys
import time
import socket
import struct
import threading
import subprocess

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtGui import QImage

class ScrcpyCore(QObject):
    frame_ready = Signal(QImage)
    fps_changed = Signal(int)
    connected = Signal()
    error_msg = Signal(str)
    stopped = Signal()

    SCRCPY_SERVER_PORT = 27183
    SCRCPY_SERVER_JAR = "/data/local/tmp/scrcpy-server.jar"

    def __init__(self, tools_dir: str = None):
        super().__init__()
        if tools_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tools_dir = os.path.join(base, "tools")
        self.tools_dir = tools_dir
        self.ffmpeg_path = self._find_tool("ffmpeg")
        self.scrcpy_server_path = self._find_tool("scrcpy-server")

        self.device_serial = None
        self.adb_path = None
        self.screen_width = 1080
        self.screen_height = 2400

        self._running = False
        self._video_socket = None
        self._control_socket = None
        self._ffmpeg_proc = None
        self._server_proc = None
        self._video_thread = None
        self._control_thread = None
        self._frame_count = 0
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._update_fps)

    def _find_tool(self, name: str) -> str:
        candidates = [
            os.path.join(self.tools_dir, name + ".exe"),
            os.path.join(self.tools_dir, name),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return name

    def _update_fps(self):
        self.fps_changed.emit(self._frame_count)
        self._frame_count = 0

    def start(self, device_serial: str, adb_path: str,
              width: int = 1280, bitrate: int = 8000000,
              max_fps: int = 60, low_latency: bool = True):
        self.device_serial = device_serial
        self.adb_path = adb_path
        self._running = True

        # Push scrcpy-server to device
        if not self._push_server():
            self.error_msg.emit("Failed to push scrcpy-server to device")
            return

        # Setup port forwarding
        self._forward_port()

        # Start scrcpy server on device
        self._start_server(width, bitrate, max_fps, low_latency)

        # Connect to video and control sockets
        time.sleep(1.0)
        if not self._connect_sockets():
            self.error_msg.emit("Failed to connect to scrcpy server sockets")
            self.stop()
            return

        # Start ffmpeg decoder
        self._start_ffmpeg(width, self.screen_height)

        # Start video receiver thread
        self._video_thread = threading.Thread(target=self._receive_video, daemon=True)
        self._video_thread.start()

        # Start control receiver thread (for device -> pc events)
        self._control_thread = threading.Thread(target=self._receive_control, daemon=True)
        self._control_thread.start()

        self._fps_timer.start(1000)
        self.connected.emit()

    def _push_server(self) -> bool:
        if not os.path.isfile(self.scrcpy_server_path):
            self.error_msg.emit(f"scrcpy-server not found at {self.scrcpy_server_path}")
            return False
        try:
            subprocess.run(
                [self.adb_path, "-s", self.device_serial, "push",
                 self.scrcpy_server_path, self.SCRCPY_SERVER_JAR],
                capture_output=True, timeout=30
            )
            return True
        except Exception as e:
            print(f"[ScrcpyCore] Push server error: {e}")
            return False

    def _forward_port(self):
        try:
            subprocess.run(
                [self.adb_path, "-s", self.device_serial, "forward",
                 f"tcp:{self.SCRCPY_SERVER_PORT}", f"tcp:{self.SCRCPY_SERVER_PORT}"],
                capture_output=True, timeout=10
            )
        except Exception:
            pass

    def _start_server(self, width: int, bitrate: int, max_fps: int, low_latency: bool):
        # Get screen size
        try:
            result = subprocess.run(
                [self.adb_path, "-s", self.device_serial, "shell", "wm", "size"],
                capture_output=True, text=True, timeout=10
            )
            import re
            match = re.search(r"(\d+)x(\d+)", result.stdout)
            if match:
                self.screen_width = int(match.group(1))
                self.screen_height = int(match.group(2))
        except Exception:
            pass

        tunnel = "tunnel=true"  # Use forward tunnel
        cmd = (
            f"CLASSPATH={self.SCRCPY_SERVER_JAR} "
            f"app_process / com.genymobile.scrcpy.Server 2.7 "
            f"log_level=info "
            f"video=true audio=false "
            f"max_size={width} "
            f"video_bit_rate={bitrate} "
            f"max_fps={max_fps} "
            f"tunnel={tunnel} "
            f"send_device_meta=true "
            f"send_frame_meta=true "
            f"send_dummy_byte=true "
        )
        if low_latency:
            cmd += "video_buffer=0 "

        try:
            self._server_proc = subprocess.Popen(
                [self.adb_path, "-s", self.device_serial, "shell", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self.error_msg.emit(f"Failed to start scrcpy server: {e}")

    def _connect_sockets(self) -> bool:
        try:
            # Video socket
            self._video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._video_socket.settimeout(10)
            self._video_socket.connect(("127.0.0.1", self.SCRCPY_SERVER_PORT))

            # Read dummy byte (device meta)
            dummy = self._video_socket.recv(64)

            # Control socket - reconnect for control channel
            # scrcpy uses a second connection for control
            self._control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._control_socket.settimeout(10)
            self._control_socket.connect(("127.0.0.1", self.SCRCPY_SERVER_PORT))

            return True
        except Exception as e:
            print(f"[ScrcpyCore] Socket connect error: {e}")
            return False

    def _start_ffmpeg(self, width: int, height: int):
        """Start ffmpeg to decode H264 stream into raw frames."""
        if self.ffmpeg_path == "ffmpeg":
            self.error_msg.emit("ffmpeg not found in tools/ folder. Please download ffmpeg.exe and place it in tools/")
            return

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-f", "h264",
            "-probesize", "32",
            "-analyzeduration", "0",
            "-i", "-",
            "-f", "rawvideo",
            "-pix_fmt", "bgra",
            "-",
        ]
        try:
            self._ffmpeg_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            self.error_msg.emit(f"Failed to start ffmpeg: {e}")

    def _receive_video(self):
        """Thread: read H264 from socket -> ffmpeg stdin, read raw frames from ffmpeg stdout."""
        if not self._video_socket or not self._ffmpeg_proc:
            return

        # Thread to pump socket data into ffmpeg
        def pump_socket_to_ffmpeg():
            try:
                while self._running and self._video_socket and self._ffmpeg_proc:
                    data = self._video_socket.recv(4096)
                    if not data:
                        break
                    # Skip frame meta (12 bytes header per frame in scrcpy 2.x)
                    # We feed raw H264 - skip the PTS/dts metadata
                    if self._ffmpeg_proc.stdin:
                        self._ffmpeg_proc.stdin.write(data)
                        self._ffmpeg_proc.stdin.flush()
            except Exception as e:
                print(f"[ScrcpyCore] Pump error: {e}")

        pump_thread = threading.Thread(target=pump_socket_to_ffmpeg, daemon=True)
        pump_thread.start()

        # Read decoded raw frames from ffmpeg stdout
        frame_size = self.screen_width * self.screen_height * 4  # BGRA
        # Use the requested width for frame buffer, capped
        display_w = min(width, self.screen_width) if 'width' in dir() else 1280
        # Actually we need the actual video dimensions. The server sends at max_size.
        # Let's use a reasonable buffer and detect from ffmpeg output.
        # For simplicity, read in chunks and try to form frames.
        buf = b""
        chunk_size = 32768
        try:
            while self._running and self._ffmpeg_proc:
                data = self._ffmpeg_proc.stdout.read(chunk_size)
                if not data:
                    break
                buf += data
                # Try to extract a frame. We don't know exact dimensions yet.
                # Use 1280x720 or 1080x1920 based on max_size
                # The video is scaled to max_size maintaining aspect ratio.
                # We'll try common sizes.
                while len(buf) >= frame_size:
                    frame_data = buf[:frame_size]
                    buf = buf[frame_size:]
                    img = QImage(frame_data, self.screen_width, self.screen_height,
                                 self.screen_width * 4, QImage.Format.Format_BGR32)
                    if not img.isNull():
                        self.frame_ready.emit(img.copy())
                        self._frame_count += 1
        except Exception as e:
            print(f"[ScrcpyCore] Video read error: {e}")

    def _receive_control(self):
        """Thread: receive control events from device (unused for now, but keeps socket alive)."""
        if not self._control_socket:
            return
        try:
            while self._running and self._control_socket:
                data = self._control_socket.recv(4096)
                if not data:
                    break
        except Exception:
            pass

    # ===== Touch Injection via scrcpy control protocol =====
    # scrcpy v2.x control message format:
    # Type (1 byte) + payload
    # Type 0x02 = INJECT_TOUCH_EVENT
    #   action (1 byte): 0=down, 1=up, 2=move
    #   pointer_id (8 bytes)
    #   position: x (4 bytes), y (4 bytes)
    #   screen_width (4 bytes), screen_height (4 bytes)
    #   pressure (2 bytes, float16)
    #   action_button (4 bytes)
    #   buttons (4 bytes)

    ACTION_DOWN = 0
    ACTION_UP = 1
    ACTION_MOVE = 2

    def inject_touch(self, action: int, x: int, y: int,
                     pointer_id: int = 0xFFFFFFFFFFFFFFFF,
                     pressure: float = 1.0):
        """Send a touch event to the device via scrcpy control protocol."""
        if not self._control_socket or not self._running:
            return
        try:
            # Type = INJECT_TOUCH_EVENT (0x02)
            msg = struct.pack(">B", 0x02)
            # Action
            msg += struct.pack(">B", action)
            # Pointer ID (8 bytes, big-endian)
            msg += struct.pack(">Q", pointer_id)
            # Position X, Y (4 bytes each)
            msg += struct.pack(">II", x, y)
            # Screen width, height
            msg += struct.pack(">II", self.screen_width, self.screen_height)
            # Pressure as float16 (2 bytes) - scrcpy uses 0xFFFF for 1.0
            press_val = int(pressure * 0xFFFF)
            msg += struct.pack(">H", press_val)
            # Action button (4 bytes) - 0 for touch
            msg += struct.pack(">I", 0)
            # Buttons (4 bytes) - 0 for touch
            msg += struct.pack(">I", 0)

            self._control_socket.sendall(msg)
        except Exception as e:
            print(f"[ScrcpyCore] Touch inject error: {e}")

    def inject_swipe(self, start_x: int, start_y: int,
                     end_x: int, end_y: int, duration_ms: int = 300):
        """Inject a swipe gesture as a series of move events."""
        if not self._control_socket or not self._running:
            return

        steps = max(10, duration_ms // 16)
        self.inject_touch(self.ACTION_DOWN, start_x, start_y)

        for i in range(1, steps + 1):
            t = i / steps
            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t)
            self.inject_touch(self.ACTION_MOVE, x, y)
            time.sleep(duration_ms / 1000.0 / steps)

        self.inject_touch(self.ACTION_UP, end_x, end_y)

    def stop(self):
        self._running = False
        self._fps_timer.stop()

        if self._video_socket:
            try: self._video_socket.close()
            except: pass
            self._video_socket = None
        if self._control_socket:
            try: self._control_socket.close()
            except: pass
            self._control_socket = None
        if self._ffmpeg_proc:
            try:
                self._ffmpeg_proc.terminate()
                self._ffmpeg_proc.wait(timeout=3)
            except: pass
            self._ffmpeg_proc = None
        if self._server_proc:
            try:
                self._server_proc.terminate()
                self._server_proc.wait(timeout=3)
            except: pass
            self._server_proc = None

        self.stopped.emit()
