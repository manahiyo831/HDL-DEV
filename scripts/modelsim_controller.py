"""
ModelSim Controller
High-level API for controlling ModelSim with socket communication
Combines GUI launcher and socket client for convenient workflow
Author: Claude Code
Date: 2026-01-14
"""

import time
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modelsim_client import ModelSimClient
from simulate_gui import ModelSimGUIRunner


class ModelSimController:
    """
    High-level controller for ModelSim automation with socket communication

    Provides convenient methods for:
    - Starting ModelSim GUI with socket server
    - Quick recompile and run workflows
    - Full control over simulation
    """

    def __init__(self,
                 project_root: Path,
                 modelsim_path: str = "C:/intelFPGA/20.1/modelsim_ase/win32aloem",
                 server_port: int = 12345):
        """
        Initialize ModelSim controller

        Args:
            project_root: Project root directory (e.g., Path("d:/Claude/Ralph_loop"))
            modelsim_path: ModelSim installation path
            server_port: Socket server port (default: 12345)
        """
        self.project_root = Path(project_root)
        self.modelsim_path = modelsim_path
        self.server_port = server_port

        # Initialize GUI runner
        self.gui_runner = ModelSimGUIRunner(modelsim_path=modelsim_path)

        # Initialize client (not connected yet)
        self.client: Optional[ModelSimClient] = None

        # Store current design info
        self.design_files: List[Path] = []
        self.testbench_file: Optional[Path] = None
        self.top_module: str = ""

    def start_gui_with_server(self,
                             design_files: List[Path],
                             testbench_file: Path,
                             top_module: str,
                             sim_time: str = "1us",
                             auto_connect: bool = True,
                             connect_delay: float = 3.0) -> bool:
        """
        Start ModelSim GUI with socket server enabled

        Args:
            design_files: List of design file paths
            testbench_file: Testbench file path
            top_module: Top module name
            sim_time: Initial simulation time
            auto_connect: Automatically connect client after launch (default: True)
            connect_delay: Delay before connecting in seconds (default: 3.0)

        Returns:
            True if launched and connected successfully, False otherwise
        """
        # Store design info
        self.design_files = design_files
        self.testbench_file = testbench_file
        self.top_module = top_module

        # Launch ModelSim GUI with server
        print("="*60)
        print("Launching ModelSim GUI with socket server...")
        print("="*60)

        process = self.gui_runner.run_simulation_gui_with_server(
            design_files=[str(f) for f in design_files],
            testbench_file=str(testbench_file),
            top_module=top_module,
            sim_time=sim_time,
            server_port=self.server_port
        )

        if not process:
            print("✗ Failed to launch ModelSim GUI")
            return False

        print(f"✓ ModelSim GUI launched (PID: {process.pid})")

        # Auto-connect if requested
        if auto_connect:
            print(f"\nWaiting {connect_delay} seconds for server to start...")
            time.sleep(connect_delay)

            print("\nConnecting to socket server...")
            if self.connect():
                print("✓ Connected to ModelSim socket server")
                return True
            else:
                print("✗ Failed to connect to socket server")
                print("  You can try connecting manually later:")
                print("  controller.connect()")
                return False

        return True

    def connect(self, max_retries: int = 10, retry_delay: float = 1.0) -> bool:
        """
        Connect to ModelSim socket server

        Args:
            max_retries: Maximum connection attempts
            retry_delay: Delay between retries in seconds

        Returns:
            True if connected successfully, False otherwise
        """
        if self.client and self.client.is_connected():
            print("Already connected to ModelSim")
            return True

        self.client = ModelSimClient(port=self.server_port)
        return self.client.connect(max_retries=max_retries, retry_delay=retry_delay)

    def disconnect(self):
        """Disconnect from ModelSim socket server"""
        if self.client:
            self.client.disconnect()
            self.client = None

    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self.client is not None and self.client.is_connected()

    def ping(self) -> bool:
        """
        Ping server to check connection

        Returns:
            True if server responds, False otherwise
        """
        if not self.is_connected():
            print("Not connected to ModelSim server")
            return False

        return self.client.ping()

    def quick_recompile_and_run(self,
                                design_files: Optional[List[Path]] = None,
                                testbench_file: Optional[Path] = None,
                                sim_time: str = "1us",
                                restart: bool = True,
                                refresh_wave: bool = True) -> Dict[str, Any]:
        """
        Quick workflow: recompile -> restart -> run -> refresh waveform

        Args:
            design_files: Design files (uses stored if None)
            testbench_file: Testbench file (uses stored if None)
            sim_time: Simulation time
            restart: Restart simulation after recompile (default: True)
            refresh_wave: Refresh waveform after run (default: True)

        Returns:
            Dictionary with results of each step
        """
        if not self.is_connected():
            return {
                "success": False,
                "message": "Not connected to ModelSim server",
                "recompile": {},
                "restart": {},
                "run": {},
                "wave_refresh": {}
            }

        # Use stored design files if not provided
        if design_files is None:
            design_files = self.design_files
        if testbench_file is None:
            testbench_file = self.testbench_file

        if not design_files or not testbench_file:
            return {
                "success": False,
                "message": "No design files specified",
                "recompile": {},
                "restart": {},
                "run": {},
                "wave_refresh": {}
            }

        results = {
            "recompile": {},
            "restart": {},
            "run": {},
            "wave_refresh": {}
        }

        print("="*60)
        print("Quick Recompile and Run")
        print("="*60)

        # Step 1: Recompile
        print("\n[1/4] Recompiling...")
        recompile_result = self.client.recompile(
            design_files=[str(f) for f in design_files],
            testbench_file=str(testbench_file)
        )
        results["recompile"] = recompile_result

        if not recompile_result.get("success"):
            print("✗ Compilation failed")
            self.client.print_response(recompile_result)
            results["success"] = False
            results["message"] = "Compilation failed"
            return results

        print("✓ Compilation successful")

        # Step 2: Restart (if enabled)
        if restart:
            print("\n[2/4] Restarting simulation...")
            restart_result = self.client.restart_simulation()
            results["restart"] = restart_result

            if not restart_result.get("success"):
                print("✗ Restart failed")
                self.client.print_response(restart_result)
                results["success"] = False
                results["message"] = "Restart failed"
                return results

            print("✓ Simulation restarted")
        else:
            print("\n[2/4] Skipping restart")

        # Step 3: Run
        print(f"\n[3/4] Running simulation for {sim_time}...")
        run_result = self.client.run_simulation(sim_time)
        results["run"] = run_result

        if not run_result.get("success"):
            print("✗ Simulation run failed")
            self.client.print_response(run_result)
            results["success"] = False
            results["message"] = "Simulation run failed"
            return results

        print("✓ Simulation completed")

        # Step 4: Refresh waveform (if enabled)
        if refresh_wave:
            print("\n[4/4] Refreshing waveform...")
            wave_result = self.client.refresh_waveform()
            results["wave_refresh"] = wave_result

            if not wave_result.get("success"):
                print("⚠ Waveform refresh had warnings")
                self.client.print_response(wave_result)
            else:
                print("✓ Waveform refreshed")
        else:
            print("\n[4/4] Skipping waveform refresh")

        print("\n" + "="*60)
        print("✓ Quick recompile and run completed successfully!")
        print("="*60)

        results["success"] = True
        results["message"] = "All steps completed successfully"
        return results

    def recompile(self,
                 design_files: Optional[List[Path]] = None,
                 testbench_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Recompile design files

        Args:
            design_files: Design files (uses stored if None)
            testbench_file: Testbench file (uses stored if None)

        Returns:
            Response dictionary
        """
        if not self.is_connected():
            return {
                "success": False,
                "message": "Not connected to ModelSim server",
                "output": "",
                "errors": ["Not connected"],
                "warnings": []
            }

        if design_files is None:
            design_files = self.design_files
        if testbench_file is None:
            testbench_file = self.testbench_file

        # Convert paths to forward slash format (ModelSim requirement)
        # Also convert to relative paths from sim/ directory
        design_files_str = []
        for f in design_files:
            f_path = Path(f)
            if f_path.is_absolute():
                try:
                    rel = f_path.relative_to(self.project_root)
                    design_files_str.append(f"../{str(rel).replace(chr(92), '/')}")
                except ValueError:
                    design_files_str.append(str(f_path).replace("\\", "/"))
            else:
                design_files_str.append(f"../{str(f).replace(chr(92), '/')}")

        if testbench_file:
            tb_path = Path(testbench_file)
            if tb_path.is_absolute():
                try:
                    tb_rel = tb_path.relative_to(self.project_root)
                    testbench_str = f"../{str(tb_rel).replace(chr(92), '/')}"
                except ValueError:
                    testbench_str = str(tb_path).replace("\\", "/")
            else:
                testbench_str = f"../{str(testbench_file).replace(chr(92), '/')}"
        else:
            testbench_str = ""

        return self.client.recompile(
            design_files=design_files_str,
            testbench_file=testbench_str
        )

    def restart(self) -> Dict[str, Any]:
        """Restart simulation"""
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}
        return self.client.restart_simulation()

    def run(self, time: str) -> Dict[str, Any]:
        """Run simulation for specified time"""
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}
        return self.client.run_simulation(time)

    def refresh_waveform(self) -> Dict[str, Any]:
        """Refresh waveform display"""
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}
        return self.client.refresh_waveform()

    def execute_tcl(self, tcl_code: str) -> Dict[str, Any]:
        """Execute arbitrary TCL command"""
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}
        return self.client.execute_tcl(tcl_code)

    def shutdown_server(self):
        """Shutdown socket server (ModelSim continues running)"""
        if self.is_connected():
            result = self.client.shutdown_server()
            self.client = None
            return result
        return {"success": False, "message": "Not connected"}

    def print_response(self, response: Dict[str, Any]):
        """Pretty print response from server"""
        if self.client:
            self.client.print_response(response)

    def read_transcript(self, lines: Optional[int] = None) -> str:
        """
        Read ModelSim transcript file

        Args:
            lines: Number of lines to read from end (None = all)

        Returns:
            Transcript content
        """
        transcript_path = self.project_root / "sim" / "transcript"

        if not transcript_path.exists():
            return ""

        try:
            content = transcript_path.read_text(encoding='utf-8', errors='ignore')

            if lines:
                # Return last N lines
                all_lines = content.splitlines()
                return '\n'.join(all_lines[-lines:])

            return content
        except Exception as e:
            print(f"Warning: Could not read transcript: {e}")
            return ""

    def check_for_errors(self, transcript: Optional[str] = None) -> Dict[str, Any]:
        """
        Check transcript for compilation or simulation errors

        Args:
            transcript: Transcript content (reads if None)

        Returns:
            Dictionary with error analysis
        """
        if transcript is None:
            transcript = self.read_transcript()

        errors = []
        warnings = []

        for line in transcript.splitlines():
            line_lower = line.lower()

            # Detect errors
            if '** error' in line_lower or 'error:' in line_lower:
                errors.append(line.strip())

            # Detect warnings
            elif '** warning' in line_lower or 'warning:' in line_lower:
                warnings.append(line.strip())

        return {
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': errors,
            'warnings': warnings
        }

    def find_test_results(self, transcript: Optional[str] = None) -> Dict[str, Any]:
        """
        Find test results in transcript (looks for TEST_RESULT: markers)

        Args:
            transcript: Transcript content (reads if None)

        Returns:
            Dictionary with test results
        """
        if transcript is None:
            transcript = self.read_transcript()

        results = {
            'found': False,
            'passed': False,
            'message': '',
            'all_results': []
        }

        for line in transcript.splitlines():
            if 'TEST_RESULT:' in line:
                results['found'] = True
                results['all_results'].append(line.strip())

                if 'PASS' in line:
                    results['passed'] = True
                    results['message'] = line.strip()
                elif 'FAIL' in line:
                    results['passed'] = False
                    results['message'] = line.strip()

        return results

    def analyze_simulation(self, verbose: bool = False, recent_only: bool = True) -> Dict[str, Any]:
        """
        Analyze simulation results from transcript

        Args:
            verbose: Print detailed analysis
            recent_only: Only analyze recent content (last 100 lines)

        Returns:
            Complete analysis dictionary
        """
        if recent_only:
            # Analyze only recent simulation (last 100 lines)
            transcript = self.read_transcript(lines=100)
        else:
            transcript = self.read_transcript()

        error_check = self.check_for_errors(transcript)
        test_results = self.find_test_results(transcript)

        analysis = {
            'transcript_length': len(transcript),
            'errors': error_check,
            'test_results': test_results,
            'success': not error_check['has_errors'] and (
                not test_results['found'] or test_results['passed']
            )
        }

        if verbose:
            print("=" * 60)
            print("Simulation Analysis")
            print("=" * 60)

            if error_check['has_errors']:
                print(f"\n✗ Errors detected: {error_check['error_count']}")
                for err in error_check['errors'][:5]:  # Show first 5
                    print(f"  - {err}")
            else:
                print("\n✓ No compilation/simulation errors")

            if error_check['has_warnings']:
                print(f"\n⚠ Warnings: {error_check['warning_count']}")
                for warn in error_check['warnings'][:3]:  # Show first 3
                    print(f"  - {warn}")

            if test_results['found']:
                print(f"\n{'✓' if test_results['passed'] else '✗'} Test Results:")
                print(f"  {test_results['message']}")
            else:
                print("\nℹ No TEST_RESULT markers found")

            print(f"\nOverall: {'SUCCESS' if analysis['success'] else 'FAILED'}")
            print("=" * 60)

        return analysis


def main():
    """Example usage of ModelSim controller"""
    from pathlib import Path

    # Initialize controller
    project_root = Path("d:/Claude/Ralph_loop")
    controller = ModelSimController(project_root)

    # Example 1: Start ModelSim GUI with server (first time only)
    print("="*60)
    print("Example 1: Starting ModelSim GUI with Socket Server")
    print("="*60)

    design_files = [project_root / "hdl" / "design" / "counter.v"]
    testbench_file = project_root / "hdl" / "testbench" / "counter_tb.v"

    success = controller.start_gui_with_server(
        design_files=design_files,
        testbench_file=testbench_file,
        top_module="counter_tb",
        sim_time="1us"
    )

    if not success:
        print("\n✗ Failed to start ModelSim or connect to server")
        return

    # Wait for user to verify GUI is ready
    input("\nPress Enter when ModelSim GUI is ready...")

    # Example 2: Quick recompile and run (after HDL modification)
    print("\n" + "="*60)
    print("Example 2: Quick Recompile and Run")
    print("="*60)
    print("Simulating HDL modification...")
    print("(In real usage, you would modify HDL files here)")
    input("Press Enter to continue with recompile...")

    result = controller.quick_recompile_and_run(sim_time="1us")

    if result["success"]:
        print("\n✓ SUCCESS: Complete workflow finished")
    else:
        print(f"\n✗ FAILED: {result['message']}")

    # Example 3: Manual control
    print("\n" + "="*60)
    print("Example 3: Manual Control")
    print("="*60)

    print("\nExecuting custom TCL command...")
    tcl_result = controller.execute_tcl("pwd")
    controller.print_response(tcl_result)

    print("\nRunning additional simulation time...")
    run_result = controller.run("500ns")
    controller.print_response(run_result)

    print("\nRefreshing waveform...")
    wave_result = controller.refresh_waveform()
    controller.print_response(wave_result)

    # Cleanup
    print("\n" + "="*60)
    print("Disconnecting...")
    print("="*60)
    controller.disconnect()
    print("\nModelSim is still running. Close it manually when done.")


if __name__ == "__main__":
    main()
