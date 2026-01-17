#!/usr/bin/env python3
"""
Run simulation for specified time.

Self-contained simulation execution using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for run_sim CLI script."""
    if len(sys.argv) != 2:
        print("Usage: run_sim.py <time>")
        print()
        print("Arguments:")
        print("  time - Simulation time with units (e.g., '1us', '500ns', '10ms')")
        print()
        print("Examples:")
        print('  python run_sim.py "1us"')
        print('  python run_sim.py "500ns"')
        print('  python run_sim.py "10ms"')
        sys.exit(1)

    sim_time = sys.argv[1]

    # Get project root from current working directory
    project_root = Path.cwd()

    print(f"⏳ Running simulation for {sim_time}...")

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            print("  Make sure ModelSim is running with socket server enabled.")
            sys.exit(1)

        # Run simulation
        run_result = controller.execute_tcl(f"run {sim_time}")

        if not run_result['success']:
            print(f"✗ FAILED: Simulation run failed")
            print(f"  {run_result.get('message', 'Unknown error')}")
            controller.disconnect()
            sys.exit(1)

        print(f"✓ Simulation ran for {sim_time}")

        # Refresh waveform and bring to front
        print("⏳ Refreshing waveform...")
        controller.refresh_waveform()

        # Disconnect
        controller.disconnect()

        print()
        print(f"✓ SUCCESS: Simulation completed for {sim_time}")
        print("  Waveform refreshed and brought to front")
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