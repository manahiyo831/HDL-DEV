#!/usr/bin/env python3
"""
Change signal display format in waveform (digital radix or analog format).

Supports:
- Digital formats: binary, hex, unsigned, signed, octal, ascii
- Analog formats: analog-step, analog-interpolated (with optional height)

Self-contained format change using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


# Format categories
DIGITAL_FORMATS = ['binary', 'hex', 'unsigned', 'signed', 'octal', 'ascii']
ANALOG_FORMATS = ['analog-step', 'analog-interpolated']
VALID_FORMATS = DIGITAL_FORMATS + ANALOG_FORMATS

DEFAULT_ANALOG_HEIGHT = 80  # pixels


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


def apply_analog_format(controller, signal_path, format_type, height):
    """
    Apply analog format to signal with height and dividers.

    Args:
        controller: ModelSimController instance
        signal_path: Signal path (with leading /)
        format_type: One of ANALOG_FORMATS
        height: Height in pixels (default: 80)

    Returns:
        Result dict from execute_tcl
    """
    # Extract signal name from path for divider labels
    signal_name = signal_path.split('/')[-1]

    # Step 1: Insert divider ABOVE signal using -insert option
    divider_top = f"=== {signal_name} (analog) ==="
    result_top = controller.execute_tcl(f'wave add -divider "{divider_top}" -insert {signal_path}')
    if not result_top['success']:
        return result_top

    # Step 2: Apply analog format
    # ModelSim uses: analogstep, analoginterpolated (no hyphen!)
    tcl_format = format_type.replace('-', '')  # analog-step → analogstep
    result_format = controller.execute_tcl(f"property wave -format {tcl_format} {signal_path}")
    if not result_format['success']:
        return result_format

    # Step 3: Apply height
    result_height = controller.execute_tcl(f"property wave -height {height} {signal_path}")
    if not result_height['success']:
        return result_height

    # Step 4: Insert divider BELOW signal (simple: append to end)
    divider_bottom = f"--- {signal_name} (analog) ---"
    result_bottom = controller.execute_tcl(f'wave add -divider "{divider_bottom}"')

    # Return combined success status
    return {
        'success': True,
        'message': f'Analog format applied with dividers (format={tcl_format}, height={height})'
    }


def main():
    """Main entry point for change_wave_format CLI script."""
    if len(sys.argv) < 3:
        print("Usage: change_wave_format.py <signal_path> <format> [height]")
        print()
        print("Arguments:")
        print("  signal_path  - Full hierarchical signal path")
        print("  format       - Display format")
        print("  height       - (Optional) Height in pixels for analog formats (default: 80)")
        print()
        print("Formats:")
        print(f"  Digital (radix): {', '.join(DIGITAL_FORMATS)}")
        print(f"  Analog:          {', '.join(ANALOG_FORMATS)}")
        print()
        print("IMPORTANT: Signal path must NOT start with '/' (Git Bash issue)")
        print()
        print("Examples:")
        print('  # Digital formats')
        print('  python change_wave_format.py "counter_tb/count" "unsigned"')
        print('  python change_wave_format.py "counter_tb/data" "hex"')
        print()
        print('  # Analog formats')
        print('  python change_wave_format.py "pwm_tb/duty" "analog-step"')
        print('  python change_wave_format.py "pwm_tb/duty" "analog-step" 100')
        print('  python change_wave_format.py "pwm_tb/duty" "analog-interpolated" 120')
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
        sys.exit(1)

    # Parse optional height (for analog formats)
    height = DEFAULT_ANALOG_HEIGHT
    if len(sys.argv) > 3:
        try:
            height = int(sys.argv[3])
            if height <= 0:
                print("✗ ERROR: Height must be a positive integer")
                sys.exit(1)
        except ValueError:
            print(f"✗ ERROR: Invalid height value '{sys.argv[3]}' (must be integer)")
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
