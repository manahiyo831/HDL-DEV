#!/usr/bin/env python3
"""
Change signal display format in waveform.

Self-contained format change using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


VALID_FORMATS = ['binary', 'hex', 'unsigned', 'signed', 'octal', 'ascii']


def main():
    """Main entry point for change_wave_format CLI script."""
    if len(sys.argv) != 3:
        print("Usage: change_wave_format.py <signal_path> <format>")
        print()
        print("Arguments:")
        print("  signal_path  - Full hierarchical signal path")
        print(f"  format       - Display format: {', '.join(VALID_FORMATS)}")
        print()
        print("IMPORTANT: Signal path must NOT start with '/' (Git Bash issue)")
        print()
        print("Examples:")
        print('  python change_wave_format.py "counter_tb/count" "unsigned"')
        print('  python change_wave_format.py "counter_tb/data" "hex"')
        print('  python change_wave_format.py "counter_tb/state" "binary"')
        print()
        print("Best Practice:")
        print("  1. Run list_wave_signals.py first to get exact signal names")
        print("  2. Use the exact name from the list (without leading /)")
        sys.exit(1)

    signal_path = sys.argv[1]
    format_type = sys.argv[2].lower()

    # Validate format
    if format_type not in VALID_FORMATS:
        print(f"✗ ERROR: Invalid format '{format_type}'")
        print(f"  Valid formats: {', '.join(VALID_FORMATS)}")
        sys.exit(1)

    # Get project root from current working directory
    project_root = Path.cwd()

    print(f"⏳ Changing signal format...")
    print(f"  Signal: {signal_path}")
    print(f"  Format: {format_type}")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Ensure signal path starts with / for property wave command
        if not signal_path.startswith('/'):
            signal_path = f"/{signal_path}"

        # Build TCL command - use property wave to change radix
        tcl_cmd = f"property wave -radix {format_type} {signal_path}"
        result = controller.execute_tcl(tcl_cmd)

        # Disconnect
        controller.disconnect()

        # Check result
        if result['success']:
            print()
            print("✓ SUCCESS: Signal format changed")
            print(f"  Signal '{signal_path}' is now displayed as {format_type}")
            sys.exit(0)
        else:
            print()
            print("✗ FAILED: Could not change signal format")
            print(f"  {result.get('message', 'Unknown error')}")
            print()
            print("Tips:")
            print("  1. Run list_wave_signals.py to get exact signal name")
            print("  2. Ensure signal path does NOT start with /")
            print('  3. Example: "counter_tb/count" not "/counter_tb/count"')
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
