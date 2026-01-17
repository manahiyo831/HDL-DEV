#!/usr/bin/env python3
"""
Compile/recompile design and testbench files.

Self-contained compilation logic using controller infrastructure only.
"""

import sys
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def main():
    """Main entry point for compile CLI script."""
    if len(sys.argv) != 4:
        print("Usage: compile.py <design_file> <testbench_file> <top_module>")
        print()
        print("Arguments:")
        print("  design_file    - Path to design file (e.g., 'hdl/design/counter.v')")
        print("  testbench_file - Path to testbench file (e.g., 'hdl/testbench/counter_tb.v')")
        print("  top_module     - Top-level testbench module name")
        print()
        print("Example:")
        print('  python compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"')
        sys.exit(1)

    design_file = sys.argv[1]
    testbench_file = sys.argv[2]
    top_module = sys.argv[3]

    # Get project root from current working directory
    project_root = Path.cwd()

    print(f"⏳ Compiling design...")
    print(f"  Design:    {design_file}")
    print(f"  Testbench: {testbench_file}")
    print(f"  Top:       {top_module}")
    print()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            print("  Make sure ModelSim is running with socket server enabled.")
            print('  Run: python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim.py')
            sys.exit(1)

        # Quit existing simulation first
        print("⏳ Quitting existing simulation...")
        controller.execute_tcl("quit -sim")

        # Normalize paths (Windows backslash → forward slash)
        design_path = controller.normalize_path(design_file)
        tb_path = controller.normalize_path(testbench_file)

        # Compile design file
        print("⏳ Compiling design file...")
        result = controller.execute_tcl(f'vlog -work work {design_path}')

        if not result['success']:
            print()
            print(f"✗ FAILED: Design compilation failed")
            print(f"  File: {design_file}")
            controller.disconnect()
            sys.exit(1)

        # Compile testbench
        print("⏳ Compiling testbench...")
        result = controller.execute_tcl(f'vlog -work work {tb_path}')

        if not result['success']:
            print()
            print(f"✗ FAILED: Testbench compilation failed")
            print(f"  File: {testbench_file}")
            controller.disconnect()
            sys.exit(1)

        # Disconnect
        controller.disconnect()

        print()
        print("✓ SUCCESS: Compilation completed")
        print(f"  Design:    {design_file}")
        print(f"  Testbench: {testbench_file}")
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