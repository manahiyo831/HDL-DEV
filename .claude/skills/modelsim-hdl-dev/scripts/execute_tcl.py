#!/usr/bin/env python3
"""
Execute arbitrary TCL command in ModelSim.

This script wraps modelsim_controller.py's execute_tcl() method for CLI usage.
Use this for commands not covered by other CLI scripts.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for execute_tcl CLI script."""
    if len(sys.argv) < 2:
        print("Usage: execute_tcl.py <tcl_command>")
        print()
        print("Executes arbitrary TCL command in ModelSim.")
        print()
        print("Arguments:")
        print("  tcl_command  - Any valid ModelSim TCL command")
        print()
        print("Examples:")
        print('  python execute_tcl.py "pwd"')
        print('  python execute_tcl.py "radix -hex /counter_tb/count"')
        print('  python execute_tcl.py "wave zoom range 100ns 500ns"')
        print('  python execute_tcl.py "examine /counter_tb/count"')
        print()
        print("Use Cases:")
        print("  - Commands not covered by other CLI scripts")
        print("  - Testing new TCL commands")
        print("  - Advanced debugging operations")
        sys.exit(1)

    # Get TCL command from arguments
    tcl_command = ' '.join(sys.argv[1:])

    # Get project root from current working directory
    project_root = Path.cwd()

    print(f"⏳ Executing TCL command...")
    print(f"  Command: {tcl_command}")
    print()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Execute TCL command
        result = controller.execute_tcl(tcl_command)

        # Disconnect
        controller.disconnect()

        # Display result
        if result['success']:
            print("✓ Command executed successfully")
            print()

            # Show output if any
            if 'result' in result and result['result']:
                output = result['result'].strip()
                if output:
                    print("Output:")
                    print(output)
                    print()

            sys.exit(0)
        else:
            print("✗ Command execution failed")
            print()

            # Show error message
            if 'message' in result:
                print("Error:")
                print(f"  {result['message']}")
                print()

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
