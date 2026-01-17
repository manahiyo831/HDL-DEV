# Screenshot Capture

Capture screenshots of ModelSim panels for visual verification and documentation.

## Supported Targets

- **modelsim** - Full ModelSim window (includes all panels)
- **wave** - Waveform display panel only
- **objects** - Objects/signals list panel
- **processes** - Processes list panel
- **transcript** - Console output panel
- **sim** - Structure/Instance hierarchy panel

## Usage

```bash
# Capture waveform panel
python $SKILL/scripts/capture_screenshot.py "wave"
# Saves to: screenshots/screenshot.png

# Capture full window
python $SKILL/scripts/capture_screenshot.py "modelsim"
# Saves to: screenshots/screenshot.png (overwrites)

# Capture transcript
python $SKILL/scripts/capture_screenshot.py "transcript"
# Saves to: screenshots/screenshot.png (overwrites)

# Custom output path
python $SKILL/scripts/capture_screenshot.py "wave" "results/my_wave.png"
```

**Arguments:**
- First argument: Target panel (modelsim, wave, objects, processes, transcript, sim)
- Second argument (optional): Custom output path

**Output:**
- Default location: `screenshots/` (in current directory)
- Filename: `screenshot.png` (fixed, always overwrites)
- Custom path: Specify as second argument

## Implementation Details

**Key technique:**
- Uses Tcl `winfo id` command to get window handles from widget paths
- Direct HWND capture using Win32 BitBlt
- Works with any window size (panels are resizable)
- No coordinate conversion required