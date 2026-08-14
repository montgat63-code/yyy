# GameMaster - PUBG Controller

A low-latency screen mirroring + GameLoop-style keymapper for PUBG Mobile and mobile shooters.
Built with Python 3.11, PySide6 (Qt6), scrcpy-server, adb, and ffmpeg.

## Features

- **Screen Mirroring**: Real-time device video via scrcpy protocol, decoded with ffmpeg
- **Keymapper**: Map keyboard/mouse to on-screen touch controls
  - STEER (WASD joystick) - analog movement
  - AIM (right mouse hold + move) - camera look with sensitivity
  - FIRE (left mouse button) - shoot
  - TAP (single key) - jump, reload, crouch, etc.
  - SWIPE (key press) - scope drag gesture
- **PUBG Mobile Preset** included by default
- **Edit Mode**: drag keys to match your phone's button positions
- **Save/Load Profiles**: JSON keymaps in /keymaps/ folder
- **Touch Injection**: real touch events via scrcpy control protocol (not just visual)

## Requirements

- Windows 10/11 (or Linux/macOS with modifications)
- Python 3.11 or higher
- An Android phone with USB debugging enabled
- USB cable to connect phone to PC

## Setup Instructions

### Step 1: Install Python

Download and install Python 3.11+ from https://www.python.org/downloads/
Make sure to check "Add Python to PATH" during installation.

### Step 2: Download Required Binaries

You need to download three free tools and place them in the `tools/` folder:

1. **ADB (Android Debug Bridge)**
   - Download from: https://dl.google.com/android/repository/platform-tools-latest-windows.zip
   - Extract and copy these files to the `tools/` folder:
     - `adb.exe`
     - `AdbWinApi.dll`
     - `AdbWinUsbApi.dll`

2. **FFmpeg**
   - Download from: https://www.gyan.dev/ffmpeg/builds/ (get the "essentials" build)
   - Extract and copy `ffmpeg.exe` to the `tools/` folder

3. **scrcpy-server**
   - Download scrcpy from: https://github.com/Genymobile/scrcpy/releases
   - Extract and copy `scrcpy-server` (or `scrcpy-server.jar`) to the `tools/` folder

After downloading, your `tools/` folder should contain:
```
tools/
  adb.exe
  AdbWinApi.dll
  AdbWinUsbApi.dll
  ffmpeg.exe
  scrcpy-server
```

### Step 3: Enable USB Debugging on Your Phone

1. Go to Settings > About Phone
2. Tap "Build Number" 7 times to unlock Developer Options
3. Go to Settings > Developer Options
4. Enable "USB Debugging"
5. Connect your phone via USB cable
6. Allow USB debugging when prompted on your phone

### Step 4: Run GameMaster

**On Windows:**
- Double-click `run.bat`
- Or open a terminal and run:
  ```
  pip install -r requirements.txt
  python main.py
  ```

**On Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

## How to Use

1. Connect your Android phone via USB
2. Select your device from the dropdown (auto-detected)
3. Choose resolution (720p/1080p), FPS (30/60), and bitrate
4. Click **Start** to begin screen mirroring
5. The PUBG Mobile keymap loads automatically
6. Use keyboard/mouse to control your game:
   - WASD = Move
   - Right Click (hold) = Aim/Look around
   - Left Click = Fire
   - Space = Jump, C = Crouch, Z = Prone
   - R = Reload, F = Interact
   - Q/E = Lean, Shift = Sprint
   - 1/2/3 = Weapons, 4/5 = Grenades
   - M = Map, V = Scope
7. Press **Ctrl+H** to show/hide the key overlay
8. Click **Edit Keymap** to drag keys to match your game's buttons
9. Right-click a key in edit mode to delete it
10. Save your custom layout as a JSON profile

## File Structure

```
GameMaster/
  main.py              <- Entry point (run this)
  requirements.txt     <- Python dependencies
  run.bat              <- Windows launcher
  run.sh               <- Linux/macOS launcher
  tools/               <- Place adb, ffmpeg, scrcpy-server here
  keymaps/             <- JSON keymap profiles
    PUBG_Mobile.json
  src/
    __init__.py
    device_manager.py  <- ADB device management
    scrcpy_core.py     <- Video streaming + touch injection
    keymapper.py       <- Key/mouse mapping logic
    main_window.py     <- PySide6 UI
```

## Troubleshooting

**"ffmpeg not found"**
- Make sure `ffmpeg.exe` is in the `tools/` folder (not in a subfolder)

**"adb not found"**
- Make sure `adb.exe` and both DLL files are in the `tools/` folder

**"No device found"**
- Make sure USB debugging is enabled
- Try a different USB cable or port
- Run `tools/adb.exe devices` in a terminal to check

**Black screen when streaming**
- Make sure scrcpy-server is in the `tools/` folder
- Try lowering the resolution to 720p
- Try lowering the bitrate

**Touch injection not working**
- Make sure you pressed "Start" first
- The keymapper only activates when streaming is active

## Disclaimer

This tool is for educational purposes and accessibility use. It mirrors your own device screen and maps keyboard/mouse inputs to touch events on your own device. It does not modify game files or provide any unfair advantage.
