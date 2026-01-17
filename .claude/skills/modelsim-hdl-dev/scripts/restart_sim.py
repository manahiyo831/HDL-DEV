#!/usr/bin/env python3
"""
Restart simulation from time 0.

Self-contained restart logic using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for restart_sim CLI script."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Usage: restart_sim.py")
        print()
        print("Restarts simulation from time 0.")
        print("Waveforms are kept intact.")
        print("No arguments required.")
        sys.exit(0)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Restarting simulation...")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Restart simulation
        result = controller.execute_tcl("restart -f")

        # Disconnect
        controller.disconnect()

        # Check result
        if result['success']:
            print()
            print("✓ SUCCESS: Simulation restarted from time 0")
            print("  Waveforms are intact")
            sys.exit(0)
        else:
            print()
            error_msg = controller.analyze_error(result, context="simulation")
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
