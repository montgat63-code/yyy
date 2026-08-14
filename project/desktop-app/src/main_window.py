"""
MainWindow - PySide6 dark gaming themed UI for GameMaster.
Left panel: device + video settings. Center: video + key overlay. Right: keymap editor.
"""
import os
import sys
import json

from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QPointF
from PySide6.QtGui import (QPixmap, QImage, QPainter, QColor, QFont, QPen,
                            QBrush, QAction, QKeySequence)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QCheckBox, QGroupBox, QScrollArea, QFileDialog,
    QSpinBox, QStatusBar, QToolBar, QSizePolicy, QFrame, QGridLayout,
    QDialog, QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QStatusBar, QSplitter
)

from .scrcpy_core import ScrcpyCore
from .device_manager import DeviceManager
from .keymapper import Keymapper, KeymapProfile, KeyBinding


# ===== Styling =====
DARK_STYLE = """
QMainWindow, QWidget { background-color: #0f172a; color: #e2e8f0; }
QGroupBox {
    border: 1px solid #1e293b; border-radius: 8px;
    margin-top: 12px; padding-top: 12px;
    font-weight: bold; color: #94a3b8;
}
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QPushButton {
    background-color: #1e293b; border: 1px solid #334155;
    border-radius: 6px; padding: 6px 14px; color: #e2e8f0;
    font-weight: 600;
}
QPushButton:hover { background-color: #334155; border-color: #475569; }
QPushButton:pressed { background-color: #475569; }
QPushButton#primary {
    background-color: #06b6d4; border: none; color: white;
    font-weight: bold; border-radius: 6px; padding: 8px 20px;
}
QPushButton#primary:hover { background-color: #22d3ee; }
QPushButton#danger {
    background-color: #ef4444; border: none; color: white;
    font-weight: bold; border-radius: 6px; padding: 8px 20px;
}
QPushButton#danger:hover { background-color: #f87171; }
QPushButton#amber {
    background-color: #f59e0b; border: none; color: white;
    font-weight: bold; border-radius: 6px; padding: 8px 20px;
}
QPushButton#amber:hover { background-color: #fbbf24; }
QSlider::groove:horizontal {
    border: none; height: 4px; background: #1e293b; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #22d3ee; border: none; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #67e8f9; }
QComboBox {
    background-color: #1e293b; border: 1px solid #334155;
    border-radius: 6px; padding: 4px 10px; color: #e2e8f0;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #1e293b; border: 1px solid #334155;
    selection-background-color: #06b6d4; color: #e2e8f0;
}
QCheckBox { color: #e2e8f0; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #334155; background: #1e293b;
}
QCheckBox::indicator:checked {
    background: #06b6d4; border-color: #06b6d4;
}
QLineEdit {
    background-color: #1e293b; border: 1px solid #334155;
    border-radius: 4px; padding: 4px 8px; color: #e2e8f0;
}
QListWidget {
    background-color: #0f172a; border: 1px solid #1e293b;
    border-radius: 6px; color: #e2e8f0;
}
QListWidget::item:selected { background-color: #06b6d433; }
QListWidget::item:hover { background-color: #1e293b; }
QLabel#title { font-size: 14px; font-weight: bold; color: #ffffff; }
QLabel#subtitle { font-size: 10px; color: #64748b; }
QLabel#section { font-size: 11px; font-weight: bold; color: #64748b; }
QStatusBar { background-color: #020617; border-top: 1px solid #1e293b; }
QFrame#panel { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; }
"""


TYPE_COLORS = {
    "steer": "#22d3ee",
    "aim": "#f59e0b",
    "fire": "#ef4444",
    "tap": "#10b981",
    "swipe": "#a855f7",
}

TYPE_LABELS = {
    "steer": "Steer (Joystick)",
    "aim": "Aim (Mouse Look)",
    "fire": "Fire (Shoot)",
    "tap": "Tap (Action)",
    "swipe": "Swipe (Scope)",
}


class VideoWidget(QWidget):
    """Custom widget that displays the decoded video frame + key overlay."""
    frame_received = Signal()
    key_dragged = Signal(str, float, float)  # id, x%, y%
    key_selected = Signal(str)
    key_deleted = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 600)
        self.setMouseTracking(True)
        self.current_frame = None
        self.keys = []
        self.show_keys = True
        self.edit_mode = False
        self.selected_id = None
        self.key_opacity = 0.7
        self.key_size_scale = 1.0
        self._dragging_key = None
        self._drag_offset = QPoint(0, 0)
        self._screen_w = 1080
        self._screen_h = 2400

    def set_frame(self, img: QImage):
        self.current_frame = img
        self.update()

    def set_keys(self, keys, screen_w, screen_h):
        self.keys = keys
        self._screen_w = screen_w
        self._screen_h = screen_h
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Black background
        painter.fillRect(self.rect(), QColor("#000000"))

        if self.current_frame and not self.current_frame.isNull():
            # Scale frame to fit widget keeping aspect ratio
            pix = QPixmap.fromImage(self.current_frame)
            scaled = pix.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            # Placeholder
            painter.setPen(QColor("#475569"))
            painter.setFont(QFont("Arial", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Stream Active\nPress Start to begin")

        # Draw keys overlay
        if self.show_keys:
            self._draw_keys(painter)

        # Edit mode grid
        if self.edit_mode:
            painter.setPen(QPen(QColor(34, 211, 238, 20), 1))
            for x in range(0, self.width(), 40):
                painter.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 40):
                painter.drawLine(0, y, self.width(), y)

            # Banner
            painter.setPen(QColor("#f59e0b"))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            banner_rect = self.rect().adjusted(0, 10, 0, -self.height() + 35)
            painter.drawText(self.rect().adjusted(0, 8, 0, 0), Qt.AlignHCenter | Qt.AlignTop,
                           "Edit Mode - Drag keys, right-click to delete")

    def _draw_keys(self, painter: QPainter):
        for k in self.keys:
            x = int(k.x / 100.0 * self.width())
            y = int(k.y / 100.0 * self.height())
            size = int(k.size * self.key_size_scale)
            color = QColor(TYPE_COLORS.get(k.type, "#22d3ee"))

            if self.edit_mode:
                alpha = 255
            else:
                alpha = int(255 * self.key_opacity)

            color.setAlpha(alpha)
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), alpha // 5)))

            # Draw circle
            painter.drawEllipse(QPointF(x, y), size / 2, size / 2)

            # Selection highlight
            if self.selected_id == k.id:
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(x, y), size / 2 + 4, size / 2 + 4)

            # Key text
            painter.setPen(color)
            painter.setFont(QFont("Arial", max(8, size // 6), QFont.Bold))
            painter.drawText(QRectF(x - size / 2, y - size / 4, size, size / 2),
                           Qt.AlignCenter, k.key)

            if self.edit_mode:
                painter.setPen(QColor("#94a3b8"))
                painter.setFont(QFont("Arial", 7))
                painter.drawText(QRectF(x - size / 2, y + size / 4, size, size / 3),
                               Qt.AlignCenter, k.label)

    def _hit_test(self, pos: QPoint) -> 'KeyBinding':
        for k in reversed(self.keys):
            x = int(k.x / 100.0 * self.width())
            y = int(k.y / 100.0 * self.height())
            size = int(k.size * self.key_size_scale)
            dx = pos.x() - x
            dy = pos.y() - y
            if dx * dx + dy * dy <= (size / 2) ** 2:
                return k
        return None

    def mousePressEvent(self, event):
        if not self.edit_mode:
            return
        key = self._hit_test(event.position().toPoint())
        if event.button() == Qt.LeftButton:
            if key:
                self.selected_id = key.id
                self._dragging_key = key
                kx = int(key.x / 100.0 * self.width())
                ky = int(key.y / 100.0 * self.height())
                self._drag_offset = QPoint(event.position().toPoint().x() - kx,
                                           event.position().toPoint().y() - ky)
                self.key_selected.emit(key.id)
                self.update()
        elif event.button() == Qt.RightButton:
            if key:
                self.key_deleted.emit(key.id)

    def mouseMoveEvent(self, event):
        if not self.edit_mode or not self._dragging_key:
            return
        pos = event.position().toPoint()
        x = (pos.x() - self._drag_offset.x()) / self.width() * 100
        y = (pos.y() - self._drag_offset.y()) / self.height() * 100
        x = max(0, min(100, x))
        y = max(0, min(100, y))
        self._dragging_key.x = x
        self._dragging_key.y = y
        self.key_dragged.emit(self._dragging_key.id, x, y)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging_key = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameMaster - PUBG Controller")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(DARK_STYLE)

        # Core components
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tools_dir = os.path.join(base, "tools")
        self.keymaps_dir = os.path.join(base, "keymaps")

        self.device_mgr = DeviceManager(self.tools_dir)
        self.scrcpy = ScrcpyCore(self.tools_dir)
        self.keymapper = Keymapper(self.scrcpy)

        self.current_profile = None
        self.edit_mode = False
        self.streaming = False

        # Connect signals
        self.scrcpy.frame_ready.connect(self._on_frame)
        self.scrcpy.fps_changed.connect(self._on_fps)
        self.scrcpy.connected.connect(self._on_scrcpy_connected)
        self.scrcpy.error_msg.connect(self._on_error)
        self.scrcpy.stopped.connect(self._on_stopped)
        self.keymapper.key_activated.connect(self._on_key_activated)

        self._init_ui()
        self._refresh_devices()
        self._load_default_keymap()

        # Auto refresh devices every 3 seconds
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_devices)
        self._refresh_timer.start(3000)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left panel
        left = self._build_left_panel()
        layout.addWidget(left)

        # Center video
        center = self._build_center_panel()
        layout.addWidget(center, 1)

        # Right panel
        right = self._build_right_panel()
        layout.addWidget(right)

        # Status bar
        self.statusBar().showMessage("Ready - Connect a device and press Start")

    def _build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(260)
        panel.setStyleSheet("QFrame#panel { background-color: #0f172a; border: none; border-right: 1px solid #1e293b; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Logo
        title = QLabel("GameMaster")
        title.setObjectName("title")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #22d3ee;")
        sub = QLabel("PUBG Controller")
        sub.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addSpacing(8)

        # Device Group
        dev_group = QGroupBox("Device")
        dev_layout = QVBoxLayout(dev_group)
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(220)
        dev_layout.addWidget(self.device_combo)

        self.device_label = QLabel("No device connected")
        self.device_label.setStyleSheet("color: #64748b; font-size: 11px;")
        dev_layout.addWidget(self.device_label)

        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self._refresh_devices)
        dev_layout.addWidget(self.refresh_btn)
        layout.addWidget(dev_group)

        # Video Group
        video_group = QGroupBox("Video Settings")
        vl = QGridLayout(video_group)

        vl.addWidget(QLabel("Resolution:"), 0, 0)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["720p", "1080p"])
        self.res_combo.setCurrentIndex(1)
        vl.addWidget(self.res_combo, 0, 1)

        vl.addWidget(QLabel("Max FPS:"), 1, 0)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60"])
        self.fps_combo.setCurrentIndex(1)
        vl.addWidget(self.fps_combo, 1, 1)

        vl.addWidget(QLabel("Bitrate:"), 2, 0)
        self.bitrate_slider = QSlider(Qt.Horizontal)
        self.bitrate_slider.setRange(2, 20)
        self.bitrate_slider.setValue(8)
        self.bitrate_label = QLabel("8 Mbps")
        self.bitrate_label.setStyleSheet("color: #22d3ee;")
        self.bitrate_slider.valueChanged.connect(
            lambda v: self.bitrate_label.setText(f"{v} Mbps"))
        vl.addWidget(self.bitrate_slider, 2, 1)
        vl.addWidget(self.bitrate_label, 3, 1)

        self.low_latency_cb = QCheckBox("Low Latency Mode")
        self.low_latency_cb.setChecked(True)
        vl.addWidget(self.low_latency_cb, 4, 0, 1, 2)
        layout.addWidget(video_group)

        # Overlay Group
        overlay_group = QGroupBox("Overlay")
        ol = QVBoxLayout(overlay_group)

        self.show_keys_cb = QCheckBox("Show Keys (Ctrl+H)")
        self.show_keys_cb.setChecked(True)
        self.show_keys_cb.stateChanged.connect(self._toggle_show_keys)
        ol.addWidget(self.show_keys_cb)

        ol.addWidget(QLabel("Key Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(70)
        self.opacity_slider.valueChanged.connect(self._update_overlay)
        ol.addWidget(self.opacity_slider)

        ol.addWidget(QLabel("Key Size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 150)
        self.size_slider.setValue(100)
        self.size_slider.valueChanged.connect(self._update_overlay)
        ol.addWidget(self.size_slider)
        layout.addWidget(overlay_group)

        # Sensitivity Group
        sens_group = QGroupBox("Sensitivity")
        sl = QGridLayout(sens_group)

        sl.addWidget(QLabel("Mouse:"), 0, 0)
        self.mouse_sens = QSlider(Qt.Horizontal)
        self.mouse_sens.setRange(1, 20)
        self.mouse_sens.setValue(8)
        sl.addWidget(self.mouse_sens, 0, 1)
        self.mouse_sens_label = QLabel("8")
        self.mouse_sens_label.setStyleSheet("color: #22d3ee;")
        self.mouse_sens.valueChanged.connect(lambda v: self.mouse_sens_label.setText(str(v)))
        sl.addWidget(self.mouse_sens_label, 0, 2)

        sl.addWidget(QLabel("Aim:"), 1, 0)
        self.aim_sens = QSlider(Qt.Horizontal)
        self.aim_sens.setRange(1, 20)
        self.aim_sens.setValue(6)
        sl.addWidget(self.aim_sens, 1, 1)
        self.aim_sens_label = QLabel("6")
        self.aim_sens_label.setStyleSheet("color: #22d3ee;")
        self.aim_sens.valueChanged.connect(lambda v: self.aim_sens_label.setText(str(v)))
        sl.addWidget(self.aim_sens_label, 1, 2)
        layout.addWidget(sens_group)

        layout.addStretch()

        # Start/Stop buttons
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start_streaming)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_streaming)
        layout.addWidget(self.stop_btn)

        return panel

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_widget = VideoWidget()
        self.video_widget.key_dragged.connect(self._on_key_dragged)
        self.video_widget.key_selected.connect(self._on_key_selected)
        self.video_widget.key_deleted.connect(self._on_key_deleted)
        layout.addWidget(self.video_widget, 1)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(280)
        panel.setStyleSheet("QFrame#panel { background-color: #0f172a; border: none; border-left: 1px solid #1e293b; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Edit mode toggle
        self.edit_btn = QPushButton("Edit Keymap")
        self.edit_btn.setObjectName("amber")
        self.edit_btn.setCheckable(True)
        self.edit_btn.toggled.connect(self._toggle_edit_mode)
        layout.addWidget(self.edit_btn)

        # Add key section
        add_group = QGroupBox("Add New Key")
        al = QVBoxLayout(add_group)
        self.add_type_combo = QComboBox()
        for t, label in TYPE_LABELS.items():
            self.add_type_combo.addItem(label, t)
        al.addWidget(self.add_type_combo)

        add_row = QHBoxLayout()
        al_key_label = QLabel("Key:")
        al.addWidget(al_key_label)
        self.add_key_input = QLineEdit()
        self.add_key_input.setPlaceholderText("e.g. F, R, Space")
        al.addWidget(self.add_key_input)
        al.addLayout(add_row)

        lbl_label = QLabel("Label:")
        al.addWidget(lbl_label)
        self.add_label_input = QLineEdit()
        self.add_label_input.setPlaceholderText("e.g. Reload")
        al.addWidget(self.add_label_input)

        self.add_btn = QPushButton("+ Add Key")
        self.add_btn.clicked.connect(self._add_key)
        al.addWidget(self.add_btn)
        layout.addWidget(add_group)

        # Selected key editor
        self.sel_group = QGroupBox("Edit Selected Key")
        sl = QVBoxLayout(self.sel_group)
        self.sel_key_input = QLineEdit()
        self.sel_key_input.setPlaceholderText("Assigned key")
        sl.addWidget(QLabel("Key:"))
        sl.addWidget(self.sel_key_input)

        self.sel_label_input = QLineEdit()
        self.sel_label_input.setPlaceholderText("Label")
        sl.addWidget(QLabel("Label:"))
        sl.addWidget(self.sel_label_input)

        self.del_btn = QPushButton("Delete Key")
        self.del_btn.setObjectName("danger")
        self.del_btn.clicked.connect(self._delete_selected_key)
        sl.addWidget(self.del_btn)
        self.sel_group.setVisible(False)
        layout.addWidget(self.sel_group)

        # Key list
        list_group = QGroupBox(f"Keys")
        ll = QVBoxLayout(list_group)
        self.key_list = QListWidget()
        self.key_list.setMaximumHeight(120)
        ll.addWidget(self.key_list)
        layout.addWidget(list_group)

        # Profile management
        prof_group = QGroupBox("Profiles")
        pl = QVBoxLayout(prof_group)

        self.profile_combo = QComboBox()
        self._refresh_profile_list()
        pl.addWidget(self.profile_combo)

        btn_row = QHBoxLayout()
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self._load_profile)
        btn_row.addWidget(self.load_btn)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_profile)
        btn_row.addWidget(self.save_btn)
        pl.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._new_profile)
        btn_row2.addWidget(self.new_btn)
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._export_profile)
        btn_row2.addWidget(self.export_btn)
        pl.addLayout(btn_row2)
        layout.addWidget(prof_group)

        # Help button
        self.help_btn = QPushButton("How to Play PUBG")
        self.help_btn.clicked.connect(self._show_help)
        layout.addWidget(self.help_btn)

        layout.addStretch()

        return panel

    def _refresh_devices(self):
        devices = self.device_mgr.list_devices()
        self.device_combo.clear()
        for serial, state in devices:
            name = self.device_mgr.get_device_name(serial)
            self.device_combo.addItem(f"{name} ({serial})", serial)
        if devices:
            self.device_label.setText(f"{len(devices)} device(s) found")
            self.device_label.setStyleSheet("color: #22d3ee; font-size: 11px;")
        else:
            self.device_label.setText("No device - connect via USB & enable USB debugging")
            self.device_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _load_default_keymap(self):
        preset_path = os.path.join(self.keymaps_dir, "PUBG_Mobile.json")
        if os.path.isfile(preset_path):
            self.current_profile = self.keymapper.load_from_file(preset_path)
        if not self.current_profile:
            self.current_profile = KeymapProfile({"name": "Default", "keys": []})
        self._apply_profile_to_ui()

    def _apply_profile_to_ui(self):
        if not self.current_profile:
            return
        self.keymapper.set_profile(self.current_profile)
        self.video_widget.set_keys(
            self.current_profile.keys,
            self.keymapper.screen_w,
            self.keymapper.screen_h
        )
        self._refresh_key_list()

    def _refresh_key_list(self):
        self.key_list.clear()
        if not self.current_profile:
            return
        for k in self.current_profile.keys:
            text = f"[{k.key}] {k.label} ({k.type})"
            item = QListWidgetItem(text)
            color = QColor(TYPE_COLORS.get(k.type, "#22d3ee"))
            item.setForeground(color)
            self.key_list.addItem(item)

    def _refresh_profile_list(self):
        self.profile_combo.clear()
        if os.path.isdir(self.keymaps_dir):
            for f in os.listdir(self.keymaps_dir):
                if f.endswith(".json"):
                    name = f.replace(".json", "").replace("_", " ")
                    self.profile_combo.addItem(name, os.path.join(self.keymaps_dir, f))
        if self.current_profile:
            idx = self.profile_combo.findText(self.current_profile.name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)

    # ===== Slots =====
    def _on_frame(self, img: QImage):
        self.video_widget.set_frame(img)

    def _on_fps(self, fps: int):
        self.statusBar().showMessage(f"Streaming - FPS: {fps}")

    def _on_key_activated(self, label: str):
        self.statusBar().showMessage(f"Key activated: {label}", 2000)

    def _on_scrcpy_connected(self):
        self.statusBar().showMessage("Connected to device - video streaming")

    def _on_error(self, msg: str):
        self.statusBar().showMessage(f"Error: {msg}")
        QMessageBox.warning(self, "Error", msg)

    def _on_stopped(self):
        self.statusBar().showMessage("Stream stopped")

    def _start_streaming(self):
        if self.streaming:
            return
        serial = self.device_combo.currentData()
        if not serial:
            QMessageBox.warning(self, "No Device", "Please connect an Android device via USB first.")
            return

        self.streaming = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        width = 1280 if self.res_combo.currentText() == "720p" else 1920
        bitrate = self.bitrate_slider.value() * 1000000
        max_fps = int(self.fps_combo.currentText())

        # Get screen size
        w, h = self.device_mgr.get_screen_size(serial)
        self.keymapper.set_screen_size(w, h)
        self.video_widget.set_keys(self.current_profile.keys, w, h)

        self.scrcpy.start(
            device_serial=serial,
            adb_path=self.device_mgr.adb_path,
            width=width, bitrate=bitrate,
            max_fps=max_fps, low_latency=self.low_latency_cb.isChecked()
        )

        # Enable keymapper
        self.keymapper.mouse_sensitivity = self.mouse_sens.value()
        self.keymapper.aim_sensitivity = self.aim_sens.value()
        self.keymapper.set_enabled(True)

    def _stop_streaming(self):
        if not self.streaming:
            return
        self.streaming = False
        self.keymapper.set_enabled(False)
        self.scrcpy.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.video_widget.current_frame = None
        self.video_widget.update()

    def _toggle_show_keys(self):
        self.video_widget.show_keys = self.show_keys_cb.isChecked()
        self.video_widget.update()

    def _update_overlay(self):
        self.video_widget.key_opacity = self.opacity_slider.value() / 100.0
        self.video_widget.key_size_scale = self.size_slider.value() / 100.0
        self.video_widget.update()

    def _toggle_edit_mode(self, checked: bool):
        self.edit_mode = checked
        self.video_widget.edit_mode = checked
        self.video_widget.selected_id = None
        self.sel_group.setVisible(False)
        self.video_widget.update()

    def _add_key(self):
        if not self.current_profile:
            return
        key_type = self.add_type_combo.currentData()
        key_str = self.add_key_input.text().strip() or "F"
        label = self.add_label_input.text().strip() or "Action"
        import hashlib
        kid = hashlib.md5(f"{key_type}_{key_str}_{len(self.current_profile.keys)}".encode()).hexdigest()[:12]
        binding = KeyBinding({
            "id": kid, "type": key_type, "key": key_str,
            "label": label, "x": 50, "y": 50, "size": 50,
        })
        self.current_profile.keys.append(binding)
        self._apply_profile_to_ui()
        self.add_key_input.clear()
        self.add_label_input.clear()

    def _on_key_dragged(self, kid, x, y):
        self.video_widget.update()

    def _on_key_selected(self, kid):
        if not self.current_profile:
            return
        key = next((k for k in self.current_profile.keys if k.id == kid), None)
        if key:
            self.sel_group.setVisible(True)
            self.sel_key_input.setText(key.key)
            self.sel_label_input.setText(key.label)
            self.sel_key_input.editingFinished.connect(lambda: self._update_selected_key(key))
            self.sel_label_input.editingFinished.connect(lambda: self._update_selected_key(key))

    def _update_selected_key(self, key: KeyBinding):
        key.key = self.sel_key_input.text().strip().upper()
        key.label = self.sel_label_input.text().strip()
        self._refresh_key_list()
        self.video_widget.update()

    def _on_key_deleted(self, kid):
        if not self.current_profile:
            return
        self.current_profile.keys = [k for k in self.current_profile.keys if k.id != kid]
        self.sel_group.setVisible(False)
        self._apply_profile_to_ui()

    def _delete_selected_key(self):
        if self.video_widget.selected_id:
            self._on_key_deleted(self.video_widget.selected_id)

    def _load_profile(self):
        path = self.profile_combo.currentData()
        if path and os.path.isfile(path):
            self.current_profile = self.keymapper.load_from_file(path)
            self._apply_profile_to_ui()

    def _save_profile(self):
        if not self.current_profile:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Keymap", self.keymaps_dir, "JSON files (*.json)")
        if path:
            self.keymapper.save_to_file(path, self.current_profile)
            self._refresh_profile_list()

    def _new_profile(self):
        name = "Custom Profile"
        self.current_profile = KeymapProfile({"name": name, "keys": []})
        self._apply_profile_to_ui()
        self.edit_btn.setChecked(True)

    def _export_profile(self):
        if not self.current_profile:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Keymap", "", "JSON files (*.json)")
        if path:
            self.keymapper.save_to_file(path, self.current_profile)

    def _show_help(self):
        help_text = """GameMaster - How to Play PUBG Mobile

KEY TYPES:
- Steer (Joystick): WASD keys control movement
- Aim (Mouse Look): Hold Right Mouse Button + move mouse to look around
- Fire (Shoot): Left Mouse Button fires your weapon
- Tap (Action): Single key press for actions (Jump, Reload, Crouch, etc.)
- Swipe (Scope): Swipe gesture for scope and drag controls

DEFAULT PUBG BINDINGS:
- WASD = Move
- Right Click = Aim/Look
- Left Click = Fire
- Space = Jump
- C = Crouch
- Z = Prone
- R = Reload
- F = Interact/Pick up
- Q/E = Lean Left/Right
- Shift = Sprint
- 1/2/3 = Switch Weapons
- 4/5 = Grenades/Smoke
- M = Map
- V = Scope
- Ctrl+H = Toggle key overlay

EDITING:
- Click 'Edit Keymap' to drag keys to match your phone's buttons
- Right-click any key to delete it
- Adjust key opacity and size in the left panel
- Save custom profiles for different games

SETUP:
1. Connect Android phone via USB
2. Enable USB debugging in Developer Options
3. Select your device in the dropdown
4. Press Start to begin streaming
5. Press Stop when done
"""
        QMessageBox.information(self, "How to Play PUBG", help_text)

    def keyPressEvent(self, event):
        # Ctrl+H to toggle keys
        if event.key() == Qt.Key_H and (event.modifiers() & Qt.ControlModifier):
            self.show_keys_cb.setChecked(not self.show_keys_cb.isChecked())
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._stop_streaming()
        super().closeEvent(event)
