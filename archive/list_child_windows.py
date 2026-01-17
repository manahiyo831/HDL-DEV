#!/usr/bin/env python3
"""
List all child windows of ModelSim with detailed information
"""

import win32gui
import json

def find_modelsim_window():
    """Find ModelSim window title"""
    windows = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "ModelSim" in title:
                windows.append((hwnd, title))
        return True

    win32gui.EnumWindows(callback, None)
    return windows

def list_child_windows(parent_title: str):
    """List all child windows of a parent window

    Args:
        parent_title: Parent window title

    Returns:
        List of dicts with child window info
    """
    # Find parent window
    parent_hwnd = win32gui.FindWindow(None, parent_title)
    if parent_hwnd == 0:
        raise ValueError(f"Window not found: {parent_title}")

    children = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            children.append({
                'hwnd': hwnd,
                'class': class_name,
                'title': title,
                'x': rect[0],
                'y': rect[1],
                'width': width,
                'height': height,
                'area': width * height
            })
        return True

    win32gui.EnumChildWindows(parent_hwnd, callback, None)
    return children

def main():
    # Find ModelSim window
    modelsim_windows = find_modelsim_window()

    if not modelsim_windows:
        print("✗ No ModelSim windows found")
        return False

    parent_hwnd, parent_title = modelsim_windows[0]
    print(f"Found ModelSim: {parent_title}")
    print(f"Parent HWND: {parent_hwnd}")

    # Get parent window geometry
    parent_rect = win32gui.GetWindowRect(parent_hwnd)
    parent_width = parent_rect[2] - parent_rect[0]
    parent_height = parent_rect[3] - parent_rect[1]

    print(f"Parent size: {parent_width}x{parent_height}")
    print(f"Parent position: ({parent_rect[0]}, {parent_rect[1]})")
    print()

    # List all child windows
    children = list_child_windows(parent_title)

    # Sort by area (largest first)
    children_sorted = sorted(children, key=lambda x: x['area'], reverse=True)

    # Save to JSON file
    output_file = "modelsim_child_windows.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'parent': {
                'hwnd': parent_hwnd,
                'title': parent_title,
                'x': parent_rect[0],
                'y': parent_rect[1],
                'width': parent_width,
                'height': parent_height
            },
            'children': children_sorted
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(children)} child windows to {output_file}")
    print()

    # Display top 20 largest children
    print("Top 20 largest child windows:")
    print(f"{'#':>3} {'HWND':>10} {'Class':<40} {'Title':<30} {'Size':<15} {'Area':<10}")
    print("-" * 120)

    for i, child in enumerate(children_sorted[:20], 1):
        size_str = f"{child['width']}x{child['height']}"
        title_truncated = child['title'][:28] + '..' if len(child['title']) > 30 else child['title']
        class_truncated = child['class'][:38] + '..' if len(child['class']) > 40 else child['class']

        print(f"{i:3d} {child['hwnd']:10d} {class_truncated:<40} {title_truncated:<30} {size_str:<15} {child['area']:<10}")

    # Also save a readable text file
    text_file = "modelsim_child_windows.txt"
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(f"ModelSim Parent Window: {parent_title}\n")
        f.write(f"HWND: {parent_hwnd}\n")
        f.write(f"Size: {parent_width}x{parent_height}\n")
        f.write(f"Position: ({parent_rect[0]}, {parent_rect[1]})\n")
        f.write(f"\nTotal child windows: {len(children)}\n")
        f.write("\n" + "=" * 120 + "\n\n")

        f.write("All child windows (sorted by size):\n")
        f.write(f"{'#':>3} {'HWND':>10} {'Class':<40} {'Title':<30} {'Size':<15} {'Position':<20} {'Area':<10}\n")
        f.write("-" * 140 + "\n")

        for i, child in enumerate(children_sorted, 1):
            size_str = f"{child['width']}x{child['height']}"
            pos_str = f"({child['x']}, {child['y']})"

            f.write(f"{i:3d} {child['hwnd']:10d} {child['class']:<40} {child['title']:<30} {size_str:<15} {pos_str:<20} {child['area']:<10}\n")

    print(f"✓ Saved readable list to {text_file}")

    return True

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
