#!/usr/bin/env python3
"""
Start ModelSim GUI with socket server for a design.

Usage:
    python scripts/start_modelsim.py <design_file> <testbench_file> <top_module> [sim_time]

Example:
    python scripts/start_modelsim.py hdl/design/counter.v hdl/testbench/counter_tb.v counter_tb 1us

This script:
1. Launches ModelSim GUI
2. Compiles design and testbench
3. Loads simulation
4. Adds waveforms
5. Runs simulation
6. Starts socket server on port 12345

After this, you can use:
- quick_recompile_and_run() for iterating on the same module
- switch_module.py for switching to different modules
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modelsim_controller import ModelSimController


def start_modelsim(design_files, testbench_file, top_module, sim_time="1us"):
    """
    Start ModelSim GUI with socket server.

    Args:
        design_files: List of design file paths (can be single string or list)
        testbench_file: Path to testbench file
        top_module: Name of top-level testbench module
        sim_time: Simulation time (default: "1us")
    """
    # Convert single file to list
    if isinstance(design_files, (str, Path)):
        design_files = [design_files]

    # Convert to Path objects
    design_files = [Path(f) for f in design_files]
    testbench_file = Path(testbench_file)

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent

    print("="*60)
    print("ModelSim Startup with Socket Server")
    print("="*60)
    print(f"Design files: {[str(f) for f in design_files]}")
    print(f"Testbench: {testbench_file}")
    print(f"Top module: {top_module}")
    print(f"Simulation time: {sim_time}")
    print("")

    # Initialize controller
    controller = ModelSimController(project_root)

    print("Starting ModelSim GUI with socket server...")
    print("This will:")
    print("  1. Launch ModelSim GUI")
    print("  2. Compile design files")
    print("  3. Load simulation")
    print("  4. Add waveforms")
    print("  5. Run simulation")
    print("  6. Start socket server on port 12345")
    print("")

    try:
        controller.start_gui_with_server(
            design_files=design_files,
            testbench_file=testbench_file,
            top_module=top_module,
            sim_time=sim_time
        )

        print("\n" + "="*60)
        print("✓ ModelSim GUI started successfully!")
        print("="*60)
        print("")
        print("ModelSim is ready:")
        print("  - GUI window is open")
        print("  - Waveforms are displayed")
        print("  - Socket server is running on port 12345")
        print("")
        print("Next steps:")
        print("  - View waveforms in ModelSim GUI")
        print("  - Modify design files and use quick_recompile_and_run()")
        print("  - Switch to different module: python scripts/switch_module.py ...")
        print("")

        # Analyze initial simulation results
        print("Initial simulation results:")
        print("")

        transcript = controller.read_transcript(lines=100)

        # Extract important lines
        for line in transcript.split('\n'):
            line = line.strip()
            if any(keyword in line for keyword in ['TEST_RESULT:', 'Error:', 'Warning:']):
                print(line)

        print("")
        print("ModelSim GUI will remain open. Close it manually when done.")

        return True

    except Exception as e:
        print(f"\n✗ Failed to start ModelSim: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Command-line interface"""
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    design_file = sys.argv[1]
    testbench_file = sys.argv[2]
    top_module = sys.argv[3]
    sim_time = sys.argv[4] if len(sys.argv) > 4 else "1us"

    try:
        success = start_modelsim(design_file, testbench_file, top_module, sim_time)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
