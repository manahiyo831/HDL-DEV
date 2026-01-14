"""
Test script for ModelSim socket communication
Tests the complete workflow from GUI launch to socket control
Author: Claude Code
Date: 2026-01-14
"""

import sys
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modelsim_controller import ModelSimController


def test_basic_workflow():
    """Test basic socket communication workflow"""

    print("="*70)
    print(" ModelSim Socket Communication - Test Script")
    print("="*70)
    print()
    print("This script will:")
    print("  1. Launch ModelSim GUI with socket server")
    print("  2. Connect Python client to ModelSim")
    print("  3. Test ping command")
    print("  4. Test recompile, restart, run commands")
    print("  5. Test waveform refresh")
    print()
    print("="*70)
    print()

    # Initialize controller
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    controller = ModelSimController(
        project_root=project_root,
        modelsim_path="C:/intelFPGA/20.1/modelsim_ase/win32aloem",
        server_port=12345
    )

    # Design files
    design_files = [project_root / "hdl" / "design" / "counter.v"]
    testbench_file = project_root / "hdl" / "testbench" / "counter_tb.v"

    # Verify files exist
    print("\nVerifying design files...")
    for f in design_files:
        if not f.exists():
            print(f"✗ ERROR: File not found: {f}")
            return False
        print(f"✓ Found: {f.name}")

    if not testbench_file.exists():
        print(f"✗ ERROR: File not found: {testbench_file}")
        return False
    print(f"✓ Found: {testbench_file.name}")

    print()

    # Step 1: Launch ModelSim GUI with server
    print("="*70)
    print("STEP 1: Launching ModelSim GUI with Socket Server")
    print("="*70)
    print()

    success = controller.start_gui_with_server(
        design_files=design_files,
        testbench_file=testbench_file,
        top_module="counter_tb",
        sim_time="1us",
        auto_connect=True,
        connect_delay=5.0  # Wait 5 seconds for server to start
    )

    if not success:
        print()
        print("✗ FAILED: Could not launch ModelSim or connect to server")
        print()
        print("Troubleshooting:")
        print("  1. Check ModelSim path is correct")
        print("  2. Check ModelSim is not already running")
        print("  3. Check port 12345 is not in use")
        return False

    print()
    print("✓ SUCCESS: ModelSim launched and connected")
    print()

    # Step 2: Test ping
    print("="*70)
    print("STEP 2: Testing Ping Command")
    print("="*70)
    print()

    if controller.ping():
        print("✓ SUCCESS: Ping successful")
    else:
        print("✗ FAILED: Ping failed")
        return False

    print()

    # Step 3: Wait for user to verify GUI
    print("="*70)
    print("STEP 3: Verify ModelSim GUI")
    print("="*70)
    print()
    print("Please verify in ModelSim GUI:")
    print("  • Wave window is displayed")
    print("  • Waveform shows counter signals")
    print("  • Transcript shows 'Socket server is running on port 12345'")
    print()
    input("Press Enter when ready to continue...")
    print()

    # Step 4: Test quick recompile and run
    print("="*70)
    print("STEP 4: Testing Quick Recompile and Run")
    print("="*70)
    print()
    print("Note: This will recompile the same files and re-run simulation")
    print()

    result = controller.quick_recompile_and_run(sim_time="1us")

    if result["success"]:
        print()
        print("✓ SUCCESS: Quick recompile and run completed")
    else:
        print()
        print(f"✗ FAILED: {result['message']}")
        if "recompile" in result and not result["recompile"].get("success"):
            controller.print_response(result["recompile"])
        return False

    print()

    # Step 5: Test individual commands
    print("="*70)
    print("STEP 5: Testing Individual Commands")
    print("="*70)
    print()

    # Test execute_tcl
    print("Testing execute_tcl command...")
    tcl_result = controller.execute_tcl("puts \"Hello from Python!\"")
    if tcl_result.get("success"):
        print("✓ execute_tcl: SUCCESS")
    else:
        print("✗ execute_tcl: FAILED")
        controller.print_response(tcl_result)

    print()

    # Test run for additional time
    print("Testing run command (500ns)...")
    run_result = controller.run("500ns")
    if run_result.get("success"):
        print("✓ run: SUCCESS")
    else:
        print("✗ run: FAILED")
        controller.print_response(run_result)

    print()

    # Test waveform refresh
    print("Testing refresh_waveform command...")
    wave_result = controller.refresh_waveform()
    if wave_result.get("success"):
        print("✓ refresh_waveform: SUCCESS")
    else:
        print("✗ refresh_waveform: FAILED")
        controller.print_response(wave_result)

    print()

    # Final verification
    print("="*70)
    print("STEP 6: Final Verification")
    print("="*70)
    print()
    print("Please verify in ModelSim GUI:")
    print("  • Wave window shows updated simulation (should now be at 1.5us)")
    print("  • Transcript shows all commands executed")
    print("  • No errors in Transcript")
    print()
    input("Press Enter when verification is complete...")
    print()

    # Disconnect
    print("="*70)
    print("Test Complete - Disconnecting")
    print("="*70)
    print()
    controller.disconnect()
    print("✓ Disconnected from ModelSim")
    print()
    print("Note: ModelSim GUI is still running. Close it manually when done.")
    print()

    return True


def test_manual_connection():
    """Test connecting to already running ModelSim with socket server"""

    print("="*70)
    print(" Manual Connection Test")
    print("="*70)
    print()
    print("This test assumes ModelSim is already running with socket server")
    print()
    print("To start server manually:")
    print("  1. Open ModelSim GUI")
    print("  2. In Transcript: source scripts/modelsim_socket_server.tcl")
    print("  3. In Transcript: start_socket_server 12345")
    print()

    proceed = input("Is ModelSim running with socket server? (yes/no): ")
    if proceed.lower() not in ['yes', 'y']:
        print("Test cancelled")
        return False

    print()

    # Initialize controller
    project_root = Path(__file__).parent.parent
    controller = ModelSimController(project_root)

    # Connect
    print("Connecting to ModelSim...")
    if controller.connect():
        print("✓ Connected successfully")
    else:
        print("✗ Connection failed")
        return False

    print()

    # Test ping
    print("Testing ping...")
    if controller.ping():
        print("✓ Ping successful")
    else:
        print("✗ Ping failed")
        return False

    print()

    # Test execute_tcl
    print("Testing execute_tcl...")
    result = controller.execute_tcl("puts \"Hello from manual connection test!\"")
    controller.print_response(result)

    print()

    # Disconnect
    controller.disconnect()
    print("✓ Test complete")

    return True


def main():
    """Main test menu"""
    print()
    print("="*70)
    print(" ModelSim Socket Communication - Test Suite")
    print("="*70)
    print()
    print("Select test to run:")
    print()
    print("  1. Basic workflow (launch GUI + test all commands)")
    print("  2. Manual connection (connect to already running ModelSim)")
    print("  3. Exit")
    print()

    choice = input("Enter choice (1-3): ").strip()
    print()

    if choice == "1":
        success = test_basic_workflow()
        print()
        if success:
            print("="*70)
            print(" ✓ ALL TESTS PASSED")
            print("="*70)
        else:
            print("="*70)
            print(" ✗ TESTS FAILED")
            print("="*70)
    elif choice == "2":
        test_manual_connection()
    elif choice == "3":
        print("Exiting...")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
