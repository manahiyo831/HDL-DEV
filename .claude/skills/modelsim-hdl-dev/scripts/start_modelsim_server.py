#!/usr/bin/env python3
"""
Start ModelSim GUI with socket server only (no design loaded).

Usage:
    python scripts/start_modelsim_server.py

This script launches ModelSim GUI with a socket server on port 12345.
After this, use load_module.py (or switch_module.py) to load and simulate designs.

Benefits of this approach:
- ModelSim starts quickly (no design compilation)
- Can load/switch between multiple designs without restarting ModelSim
- More flexible workflow
"""

import sys
import subprocess
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "internal"))

from modelsim_controller import ModelSimController


def start_modelsim_server():
    """Start ModelSim GUI with socket server only."""

    # Get project root and paths
    project_root = Path.cwd()
    sim_dir = project_root / "sim"
    # TCL server script is in the SKILL internal directory
    skill_scripts_dir = Path(__file__).parent
    tcl_server_script = skill_scripts_dir / "internal" / "modelsim_socket_server.tcl"

    # ModelSim path
    MODELSIM_DEFAULT_PATH = "C:/intelFPGA/20.1/modelsim_ase/win32aloem"
    modelsim_bin = Path(MODELSIM_DEFAULT_PATH)
    vsim_exe = modelsim_bin / "vsim.exe"

    if not vsim_exe.exists():
        print(f"✗ Error: ModelSim not found at {vsim_exe}")
        print("Please update MODELSIM_DEFAULT_PATH in this script.")
        return False

    # Ensure sim directory exists
    sim_dir.mkdir(exist_ok=True)

    print("="*60)
    print("ModelSim GUI + Socket Server Startup")
    print("="*60)
    print(f"Project root: {project_root}")
    print(f"Working directory: {sim_dir}")
    print(f"Socket server: localhost:12345")
    print("")

    print("Starting ModelSim GUI...")
    print("This will:")
    print("  1. Open ModelSim GUI")
    print("  2. Start socket server on port 12345")
    print("  3. Wait for design to be loaded")
    print("")

    # Build command (convert path to forward slashes for TCL)
    tcl_script_path = str(tcl_server_script).replace("\\", "/")
    cmd = [
        str(vsim_exe),
        "-gui",
        "-do", f"source {tcl_script_path}; start_socket_server 12345"
    ]

    print(f"Executing: {' '.join(cmd)}")
    print(f"Working directory: {sim_dir}")
    print("")

    try:
        # Launch ModelSim
        process = subprocess.Popen(
            cmd,
            cwd=str(sim_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )

        print(f"✓ ModelSim GUI launched (PID: {process.pid})")
        print("")
        print("Waiting for socket server to start (up to 10 seconds)...")

        # Test connection with retry (10-second timeout)
        controller = ModelSimController(project_root)
        if controller.connect(max_retries=20, retry_delay=0.5):
            controller.disconnect()  # We just tested connection, disconnect
            print("✓ Socket server is ready")
        else:
            print("✗ Socket server failed to start within timeout")
            return False

        print("")
        print("="*60)
        print("✓ ModelSim is ready!")
        print("="*60)
        print("")
        print("ModelSim GUI Status:")
        print("  - GUI window is open")
        print("  - Socket server is running on port 12345")
        print("  - No design loaded yet")
        print("")
        print("Next steps:")
        print("  1. Load a design:")
        print("     python scripts/load_module.py hdl/design/counter.v hdl/testbench/counter_tb.v counter_tb 1us")
        print("")
        print("  2. Or use switch_module.py to load a different design:")
        print("     python scripts/switch_module.py hdl/design/new.v hdl/testbench/new_tb.v new_tb 1us")
        print("")
        print("ModelSim GUI will remain open. Close it manually when done.")
        print("")

        return True

    except Exception as e:
        print(f"✗ Failed to start ModelSim: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Command-line interface"""
    try:
        success = start_modelsim_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
