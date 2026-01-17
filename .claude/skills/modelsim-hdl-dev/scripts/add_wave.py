#!/usr/bin/env python3
"""
Add signal(s) to waveform display.

Self-contained signal addition using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for add_wave CLI script."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: add_wave.py [signal_path...]")
        print()
        print("Arguments:")
        print("  signal_path  - Signal paths to add (optional)")
        print("                 If not specified, adds all signals recursively")
        print()
        print("IMPORTANT: Signal paths must NOT start with '/' (Git Bash issue)")
        print()
        print("Examples:")
        print('  python add_wave.py                                # Add all signals')
        print('  python add_wave.py "counter_tb/count"             # Add one signal')
        print('  python add_wave.py "counter_tb/clk" "counter_tb/reset"  # Add multiple')
        sys.exit(0)

    signal_paths = sys.argv[1:] if len(sys.argv) > 1 else []

    # Get project root from current working directory
    project_root = Path.cwd()

    if signal_paths:
        print(f"⏳ Adding {len(signal_paths)} signal(s) to waveform...")
    else:
        print("⏳ Adding all signals to waveform...")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Build TCL command
        if signal_paths:
            # Add specific signals
            for signal_path in signal_paths:
                # Ensure signal path doesn't start with / (Git Bash issue)
                if signal_path.startswith('/'):
                    signal_path = signal_path[1:]

                tcl_cmd = f"add wave /{signal_path}"
                result = controller.execute_tcl(tcl_cmd)

                if result['success']:
                    print(f"  ✓ Added: {signal_path}")
                else:
                    print()
                    error_msg = controller.analyze_error(result, context="waveform")
                    print(error_msg)
                    print()
        else:
            # Add all signals recursively
            tcl_cmd = "add wave -r /*"
            result = controller.execute_tcl(tcl_cmd)

            if not result['success']:
                print()
                error_msg = controller.analyze_error(result, context="waveform")
                print(error_msg)
                controller.disconnect()
                sys.exit(1)

            print("  ✓ Added all signals recursively")

        # Disconnect
        controller.disconnect()

        print()
        print("✓ SUCCESS: Signals added to waveform")
        sys.exit(0)

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
