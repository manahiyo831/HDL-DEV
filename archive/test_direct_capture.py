#!/usr/bin/env python3
"""
Test direct child window capture using actual screen coordinates
"""

import sys
from pathlib import Path
import win32gui
import win32ui
import win32con
from PIL import Image
from datetime import datetime

def find_wave_window_by_size(target_width=1191, target_height=458):
    """Find Wave window by matching size"""

    def find_modelsim_window():
        windows = []
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "ModelSim" in title:
                    windows.append((hwnd, title))
            return True
        win32gui.EnumWindows(callback, None)
        return windows

    modelsim_windows = find_modelsim_window()
    if not modelsim_windows:
        return None

    parent_hwnd, parent_title = modelsim_windows[0]

    # Find child windows matching the target size
    candidates = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if class_name == "TkChild":
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                if width == target_width and height == target_height:
                    candidates.append({
                        'hwnd': hwnd,
                        'rect': rect,
                        'width': width,
                        'height': height
                    })
        return True

    win32gui.EnumChildWindows(parent_hwnd, callback, None)

    return candidates

def capture_child_window_direct(hwnd: int, output_path: Path) -> bool:
    """Capture child window directly using its window handle"""
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        print(f"  Window rect: ({left}, {top}, {right}, {bottom})")
        print(f"  Size: {width}x{height}")

        # Capture using GetWindowDC (captures the window contents)
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # Copy the window contents
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
        img.save(output_path)

        # Cleanup
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return True

    except Exception as e:
        print(f"✗ Capture failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("Direct Child Window Capture Test")
    print("="*60)

    # Find Wave window by size
    print("\n[1/3] Finding Wave window (1191x458)...")
    candidates = find_wave_window_by_size(1191, 458)

    if not candidates:
        print("✗ No Wave window found with size 1191x458")
        return False

    print(f"✓ Found {len(candidates)} candidate(s):")
    for i, c in enumerate(candidates, 1):
        print(f"  {i}. HWND={c['hwnd']}, Rect={c['rect']}")

    # Capture the first candidate
    print(f"\n[2/3] Capturing first candidate (HWND={candidates[0]['hwnd']})...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(f"waveform_direct_{timestamp}.png")

    success = capture_child_window_direct(candidates[0]['hwnd'], output_path)

    if not success:
        print("✗ Capture failed")
        return False

    print(f"✓ Captured successfully")

    # Verify
    print(f"\n[3/3] Verifying saved file...")
    if output_path.exists():
        file_size = output_path.stat().st_size / 1024
        img = Image.open(output_path)
        print(f"✓ File saved: {output_path}")
        print(f"  File size: {file_size:.1f} KB")
        print(f"  Image size: {img.size[0]}x{img.size[1]} pixels")
        print(f"  Image mode: {img.mode}")
    else:
        print("✗ File not found")
        return False

    print("\n" + "="*60)
    print("✅ Direct capture test successful!")
    print("="*60)
    print(f"\nScreenshot saved: {output_path.absolute()}")
    print("\nThis method:")
    print("  ✓ Uses actual screen coordinates (no Tcl needed)")
    print("  ✓ Captures Wave window directly by HWND")
    print("  ✓ Simple and reliable")

    return True

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
