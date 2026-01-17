#!/usr/bin/env python3
"""
Adjust waveform zoom level.

Self-contained zoom control using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for zoom_waveform CLI script."""
    if len(sys.argv) < 2:
        print("Usage: zoom_waveform.py <mode> [args...]")
        print()
        print("Modes:")
        print("  full              - Zoom to show entire simulation")
        print("  <start> <end>     - Zoom to specific time range")
        print()
        print("Examples:")
        print('  python zoom_waveform.py full')
        print('  python zoom_waveform.py "100ns" "500ns"')
        print('  python zoom_waveform.py "1us" "2us"')
        sys.exit(1)

    mode = sys.argv[1].lower()

    # Get project root from current working directory
    project_root = Path.cwd()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Build TCL command based on mode
        if mode == 'full':
            print("⏳ Zooming waveform to full view...")
            tcl_cmd = "wave zoom full"
        elif len(sys.argv) == 3:
            start_time = sys.argv[1]
            end_time = sys.argv[2]
            print(f"⏳ Zooming waveform to range {start_time} - {end_time}...")
            tcl_cmd = f"wave zoom range {start_time} {end_time}"
        else:
            print("✗ ERROR: Invalid arguments")
            print("  For range zoom, provide both start and end times")
            print('  Example: python zoom_waveform.py "100ns" "500ns"')
            controller.disconnect()
            sys.exit(1)

        # Execute command
        result = controller.execute_tcl(tcl_cmd)

        # Disconnect
        controller.disconnect()

        # Check result
        if result['success']:
            print()
            print("✓ SUCCESS: Waveform zoom adjusted")
            sys.exit(0)
        else:
            print()
            error_msg = controller.analyze_error(result, context="waveform")
            print(error_msg)
            sys.exit(1)

    except KeyboardInterrupt:
        print()
        print("✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
