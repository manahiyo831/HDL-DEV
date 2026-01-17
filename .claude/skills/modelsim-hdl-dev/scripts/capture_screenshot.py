#!/usr/bin/env python3
"""
ModelSim screenshot capture script
Captures screenshot of specified ModelSim panel

This module is completely self-contained and independent of ModelSimController.
It only depends on ModelSimClient for TCL command execution.

Implementation Notes:
--------------------
This implementation uses Tcl 'winfo id' to get the window handle (HWND) from
Tcl widget paths (e.g., .main_pane.wave), then captures directly using Win32 BitBlt.

Key advantages:
- No coordinate conversion needed (uses actual screen coordinates)
- Works with any window size (panels are resizable)
- Reliable across dual-monitor setups
- Simple and maintainable

Alternative approaches that were tested but not used:
1. Tcl coordinate-based capture: Failed due to complex offset calculations
2. MDIClient window search: Not applicable (ModelSim uses Tcl/Tk, not MDI)
3. Size-based window search: Works but fragile if window is resized

For future extensions:
- To capture specific sub-regions: Use widget hierarchy (.main_pane.wave.interior.cs.body.pw.wf)
- For dynamic size handling: Use winfo width/height commands
- For multiple panels: Iterate through PANEL_WIDGET_PATHS

Author: Claude Code
Date: 2026-01-17
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "internal"))

from modelsim_client import ModelSimClient


# ==========================================
# Constants
# ==========================================

PANEL_WIDGET_PATHS = {
    'wave': '.main_pane.wave',          # Waveform display
    'transcript': '.main_pane.transcript',  # Console output
    'objects': '.main_pane.objects',    # Objects/signals panel
    'processes': '.main_pane.process',  # Processes list
    'sim': '.main_pane.structure',      # Structure/Instance hierarchy
}


# ==========================================
# Helper Functions
# ==========================================

def _find_modelsim_window() -> Optional[int]:
    """
    Find ModelSim parent window HWND

    Returns:
        Parent window HWND or None if not found
    """
    import win32gui

    windows = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "ModelSim" in title:
                windows.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)
    return windows[0] if windows else None


def _get_panel_hwnd_via_tcl(client: ModelSimClient, widget_path: str) -> int:
    """
    Get panel HWND via Tcl winfo id command

    Args:
        client: Connected ModelSimClient instance
        widget_path: Tcl widget path (e.g., ".main_pane.wave")

    Returns:
        Window handle (HWND) as integer

    Raises:
        RuntimeError: If widget not found or Tcl command fails
    """
    if not client.is_connected():
        raise RuntimeError("Not connected to ModelSim")

    # Execute Tcl command to get window ID
    result = client.execute_tcl(f"winfo id {widget_path}")

    if not result.get('success'):
        raise RuntimeError(
            f"Failed to get HWND for {widget_path}: {result.get('message')}"
        )

    # Parse HWND from output (should be decimal integer or hex)
    try:
        hwnd_str = result['output'].strip()
        # Tcl returns in format like "0x12345" or decimal "74565"
        if hwnd_str.startswith('0x'):
            hwnd = int(hwnd_str, 16)
        else:
            hwnd = int(hwnd_str)
        return hwnd
    except (ValueError, KeyError) as e:
        raise RuntimeError(
            f"Failed to parse HWND from Tcl output '{result.get('output')}': {e}"
        )


def _capture_window_by_hwnd(hwnd: int, output_path: Path) -> Dict[str, Any]:
    """
    Capture window by HWND using BitBlt

    Args:
        hwnd: Window handle to capture
        output_path: Where to save screenshot

    Returns:
        Dictionary with success, image, path, width, height
    """
    import win32gui
    import win32ui
    import win32con
    from PIL import Image

    try:
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # Capture using BitBlt
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # Copy window contents
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

        # Convert to PIL Image
        bmp_info = bitmap.GetInfo()
        bmp_bits = bitmap.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_bits, 'raw', 'BGRX', 0, 1
        )

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

        return {
            'success': True,
            'image': img,
            'path': str(output_path),
            'width': width,
            'height': height
        }

    finally:
        # Cleanup resources
        try:
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
        except:
            pass  # Ignore cleanup errors


# ==========================================
# Main Capture Function
# ==========================================

def capture_screenshot(client: ModelSimClient,
                      target: str = 'wave',
                      output_path: Optional[Path] = None,
                      project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Capture screenshot of specified ModelSim panel

    Args:
        client: Connected ModelSimClient instance
        target: Panel to capture - 'modelsim', 'wave', 'objects',
               'processes', 'transcript', 'sim'
        output_path: Optional custom path
                    (default: screenshots/screenshot.png)
        project_root: Project root directory (required if output_path is None)

    Returns:
        Dictionary with keys:
        - success: bool
        - image: PIL.Image
        - path: str
        - width: int
        - height: int
        - target: str
        - message: str

    Raises:
        ValueError: If target is invalid
        RuntimeError: If ModelSim or target window not found
    """
    # Validate target
    valid_targets = ['modelsim', 'wave', 'objects', 'processes',
                    'transcript', 'sim']
    if target not in valid_targets:
        raise ValueError(
            f"Invalid target: {target}. "
            f"Must be one of: {', '.join(valid_targets)}"
        )

    # Default output path
    if output_path is None:
        if project_root is None:
            raise ValueError("project_root must be provided if output_path is None")
        output_path = project_root / 'screenshots' / 'screenshot.png'

    # Find target window
    if target == 'modelsim':
        # Capture full parent window
        parent_hwnd = _find_modelsim_window()
        if parent_hwnd is None:
            raise RuntimeError("ModelSim window not found. Is ModelSim running?")
        target_hwnd = parent_hwnd
    else:
        # Get panel HWND via Tcl winfo id command
        widget_path = PANEL_WIDGET_PATHS[target]
        target_hwnd = _get_panel_hwnd_via_tcl(client, widget_path)

    # Capture
    result = _capture_window_by_hwnd(target_hwnd, output_path)
    result['target'] = target
    result['message'] = f"Captured {target} panel to {result['path']}"

    return result


# ==========================================
# CLI Interface
# ==========================================

def main():
    """
    Capture screenshot of ModelSim panel

    Usage:
        python scripts/capture_screenshot.py [target] [output_path]

    Args:
        target: Panel to capture (wave, modelsim, objects, processes, transcript, sim)
                Default: wave
        output_path: Optional custom output path
                    Default: screenshots/screenshot.png

    Examples:
        python scripts/capture_screenshot.py "wave"
        python scripts/capture_screenshot.py "modelsim"
        python scripts/capture_screenshot.py "wave" "results/my_screenshot.png"
    """
    # Parse arguments
    target = sys.argv[1] if len(sys.argv) > 1 else 'wave'
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    # Get project root (current working directory)
    project_root = Path.cwd()

    print("="*60)
    print("ModelSim Screenshot Capture")
    print("="*60)
    print(f"Target panel: {target}")
    if output_path:
        print(f"Output path: {output_path}")
    else:
        print(f"Output path: screenshots/screenshot.png (default)")
    print()

    # Connect to ModelSim
    print("[1/3] Connecting to ModelSim...")
    client = ModelSimClient(port=12345)
    if not client.connect():
        print("✗ Failed to connect to ModelSim")
        print("\nPlease ensure ModelSim is running with socket server:")
        print("  python scripts/start_modelsim_server.py")
        print("  python scripts/load_module.py ...")
        return False

    print("✓ Connected to ModelSim")

    # Capture screenshot
    print(f"\n[2/3] Capturing {target} panel...")
    try:
        result = capture_screenshot(
            client=client,
            target=target,
            output_path=output_path,
            project_root=project_root
        )

        if result['success']:
            print(f"✓ Screenshot captured successfully!")
            print(f"  Size: {result['width']}x{result['height']} pixels")
            print(f"  Saved to: {result['path']}")
        else:
            print(f"✗ Screenshot failed: {result.get('message', 'Unknown error')}")
            return False

    except ValueError as e:
        print(f"✗ Invalid target: {e}")
        print("\nValid targets: wave, modelsim, objects, processes, transcript, sim")
        return False
    except RuntimeError as e:
        print(f"✗ Capture failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Disconnect
        print("\n[3/3] Disconnecting...")
        client.disconnect()
        print("✓ Disconnected")

    # Summary
    print("\n" + "="*60)
    print("✅ Screenshot capture complete!")
    print("="*60)
    print(f"\nScreenshot saved: {Path(result['path']).absolute()}")
    print(f"Image size: {result['width']}x{result['height']} pixels")
    print(f"\nNext time you capture, it will overwrite this file.")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
