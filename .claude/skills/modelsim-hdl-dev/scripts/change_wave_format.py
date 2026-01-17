#!/usr/bin/env python3
"""
Change signal display format in waveform (digital radix only).

Supports:
- Digital formats: binary, hex, unsigned, signed, octal, ascii

For analog display, use add_wave_analog.py instead.

Self-contained format change using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


# Format categories
DIGITAL_FORMATS = ['binary', 'hex', 'unsigned', 'signed', 'octal', 'ascii']
VALID_FORMATS = DIGITAL_FORMATS


def apply_digital_format(controller, signal_path, format_type):
    """
    Apply digital radix format to signal.

    Args:
        controller: ModelSimController instance
        signal_path: Signal path (with leading /)
        format_type: One of DIGITAL_FORMATS

    Returns:
        Result dict from execute_tcl
    """
    tcl_cmd = f"property wave -radix {format_type} {signal_path}"
    return controller.execute_tcl(tcl_cmd)


def main():
    """Main entry point for change_wave_format CLI script."""
    if len(sys.argv) < 3:
        print("Usage: change_wave_format.py <signal_path> <format>")
        print()
        print("Arguments:")
        print("  signal_path  - Full hierarchical signal path")
        print("  format       - Display format (radix)")
        print()
        print("Formats:")
        print(f"  Digital (radix): {', '.join(DIGITAL_FORMATS)}")
        print()
        print("IMPORTANT: Signal path must NOT start with '/' (Git Bash issue)")
        print()
        print("Examples:")
        print('  python change_wave_format.py "counter_tb/count" "unsigned"')
        print('  python change_wave_format.py "counter_tb/data" "hex"')
        print('  python change_wave_format.py "counter_tb/addr" "binary"')
        print()
        print("For analog display:")
        print('  Use add_wave_analog.py instead')
        print('  python add_wave_analog.py "counter_tb/count" --radix unsigned')
        print()
        print("Best Practice:")
        print("  1. Run list_wave_signals.py first to get exact signal names")
        print("  2. Use the exact name from the list (without leading /)")
        sys.exit(1)

    # Parse arguments
    signal_path = sys.argv[1]
    format_type = sys.argv[2].lower()

    # Validate format
    if format_type not in VALID_FORMATS:
        print(f"✗ ERROR: Invalid format '{format_type}'")
        print(f"  Valid formats: {', '.join(VALID_FORMATS)}")
        print()
        print("For analog display, use add_wave_analog.py instead")
        sys.exit(1)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Changing signal format...")
    print(f"  Signal: {signal_path}")
    print(f"  Format: {format_type}")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        print("Connected to ModelSim at localhost:12345")

        # Ensure signal path starts with / for property wave command
        if not signal_path.startswith('/'):
            signal_path = f"/{signal_path}"

        # Apply digital format
        result = apply_digital_format(controller, signal_path, format_type)

        # Disconnect
        controller.disconnect()
        print("Disconnected from ModelSim")

        # Check result
        if result['success']:
            print()
            print("✓ SUCCESS: Signal format changed")
            print(f"  Signal '{signal_path}' is now displayed as {format_type}")
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
