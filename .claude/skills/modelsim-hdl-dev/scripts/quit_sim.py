#!/usr/bin/env python3
"""
Quit current simulation.

This script wraps modelsim_controller.py's execute_tcl() method for quitting simulation.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for quit_sim CLI script."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: quit_sim.py")
        print()
        print("Quits current simulation.")
        print("ModelSim GUI remains open.")
        print("No arguments required.")
        sys.exit(0)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Quitting simulation...")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Quit simulation
        result = controller.execute_tcl("quit -sim")

        # Disconnect
        controller.disconnect()

        # Check result
        if result['success']:
            print()
            print("✓ SUCCESS: Simulation quit")
            print("  ModelSim GUI is still running")
            sys.exit(0)
        else:
            print()
            print("✗ FAILED: Could not quit simulation")
            print(f"  {result.get('message', 'Unknown error')}")
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
