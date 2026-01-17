#!/usr/bin/env python3
"""
Load and simulate a design in ModelSim.

Prerequisites:
    ModelSim must be running with socket server. Start it first:
        python scripts/start_modelsim_server.py

Usage:
    python scripts/load_module.py <design_file> <testbench_file> <top_module> [sim_time]

Example:
    python scripts/load_module.py hdl/design/counter.v hdl/testbench/counter_tb.v counter_tb 1us

This script:
1. Connects to running ModelSim instance
2. Exits current simulation (if any)
3. Compiles the design files
4. Loads the testbench
5. Adds waveforms
6. Runs simulation
7. Refreshes waveform display

Benefits:
- Works for both initial load and switching between designs
- ModelSim stays running for fast iteration
- Clear workflow: start server once, then load/switch designs as needed
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "internal"))

from modelsim_controller import ModelSimController


def load_module(design_files, testbench_file, top_module, sim_time="1us"):
    """
    Load and simulate a design in ModelSim.

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

    # Get project root (current working directory)
    project_root = Path.cwd()

    print("="*60)
    print("ModelSim Module Loader")
    print("="*60)
    print(f"Design files: {[str(f) for f in design_files]}")
    print(f"Testbench: {testbench_file}")
    print(f"Top module: {top_module}")
    print(f"Simulation time: {sim_time}")
    print("")

    # Initialize controller and connect
    controller = ModelSimController(project_root)

    print("[1/7] Connecting to ModelSim...")
    connected = controller.connect()

    if not connected:
        print("")
        print("✗ Cannot connect to ModelSim")
        print("")
        print("Please start ModelSim first:")
        print("  python scripts/start_modelsim_server.py")
        print("")
        print("Then run this script again.")
        return False

    print("✓ Connected to ModelSim")

    # Step 1: Exit current simulation (if any)
    print("\n[2/7] Preparing ModelSim...")
    try:
        controller.execute_tcl('quit -sim')
        print("✓ Previous simulation cleared")
    except:
        print("✓ No previous simulation (this is OK)")

    # Step 2: Compile design
    print("\n[3/7] Compiling design files...")

    # Compile each design file
    for design_file in design_files:
        design_path = controller.normalize_path(str(design_file))
        result = controller.execute_tcl(f'vlog -work work {design_path}')
        if not result['success']:
            print(f"✗ Failed to compile {design_file}")
            return False

    # Compile testbench
    tb_path = controller.normalize_path(str(testbench_file))
    result = controller.execute_tcl(f'vlog -work work {tb_path}')
    if not result['success']:
        print(f"✗ Failed to compile testbench {testbench_file}")
        return False

    print("✓ Compilation successful")

    # Step 3: Load testbench
    print(f"\n[4/7] Loading testbench: {top_module}...")
    vsim_result = controller.execute_tcl(f'vsim work.{top_module}')
    if not vsim_result.get('success'):
        print("✗ Failed to load testbench")
        print(vsim_result)
        return False

    # Set onfinish to stop (prevent $finish dialog)
    controller.execute_tcl('onfinish stop')

    print("✓ Testbench loaded")

    # Step 4: Add waveforms
    print("\n[5/7] Adding waveforms...")
    controller.execute_tcl('add wave -r /*')
    controller.execute_tcl('wave zoom full')
    print("✓ Waveforms added")

    # Step 5: Run simulation
    print(f"\n[6/7] Running simulation for {sim_time}...")
    run_result = controller.execute_tcl(f"run {sim_time}")

    if not run_result.get('success'):
        print("✗ Simulation failed")
        print(run_result)
        return False

    print("✓ Simulation completed")

    # Step 6: Refresh waveform and bring to front
    print("\n[7/7] Refreshing waveform...")
    controller.refresh_waveform()
    print("✓ Waveform refreshed and brought to front")

    print("\n" + "="*60)
    print("✓ Design loaded and simulated successfully!")
    print("="*60)
    print("ModelSim GUI is ready with waveforms.")
    print("")

    # Analyze results
    print("Simulation results:")
    print("")

    transcript = controller.read_transcript(lines=100)

    # Extract important lines
    found_results = False
    for line in transcript.split('\n'):
        line = line.strip()
        if any(keyword in line for keyword in ['TEST_RESULT:', 'Error:', 'Warning:']):
            print(line)
            found_results = True

    if not found_results:
        print("(No TEST_RESULT markers or errors found)")

    print("")
    print("Next steps:")
    print("  - View waveforms in ModelSim GUI")
    print("  - Modify HDL files and use quick_recompile_and_run() for fast iteration")
    print("  - Load another design: python scripts/load_module.py ...")
    print("")

    return True


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
        success = load_module(design_file, testbench_file, top_module, sim_time)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
