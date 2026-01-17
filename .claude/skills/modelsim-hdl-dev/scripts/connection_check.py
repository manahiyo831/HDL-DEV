#!/usr/bin/env python3
"""
Verify connection to ModelSim socket server.

This script checks if ModelSim is running and the socket server is accessible.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for connection_check CLI script."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: connection_check.py")
        print()
        print("Checks connection to ModelSim socket server.")
        print("No arguments required.")
        sys.exit(0)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Checking connection to ModelSim socket server...")
    print()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Attempt to connect
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ FAILED: Cannot connect to ModelSim socket server")
            print()
            print("Possible causes:")
            print("  1. ModelSim is not running")
            print("  2. Socket server is not started")
            print("  3. Port 12345 is blocked or in use")
            print()
            print("Solution:")
            print('  Run: python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim.py \\')
            print('           "hdl/design/your_design.v" "hdl/testbench/your_tb.v" "tb_name" "1us"')
            sys.exit(1)

        # Send test command (get working directory)
        print("✓ Connected to ModelSim socket server")
        print()

        # Get working directory
        try:
            result = controller.execute_tcl("pwd")
            if result['success']:
                pwd = result['result'].strip()
                print(f"Working Directory: {pwd}")
        except:
            pass

        # Disconnect
        controller.disconnect()

        print()
        print("=" * 60)
        print("✓ Connection Status: OK")
        print("=" * 60)
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
