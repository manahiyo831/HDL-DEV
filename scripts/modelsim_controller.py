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

# ============================================================
# Screenshot Capture Configuration
# ============================================================
# Panel widget path mapping for Tcl winfo id command
# Note: Panel sizes are variable (user can resize), so we use Tcl widget paths
# Verified paths from ModelSim investigation (2026-01-15)
PANEL_WIDGET_PATHS = {
    'wave': '.main_pane.wave',          # Waveform display (verified: 1091x320)
    'transcript': '.main_pane.transcript',  # Console output (verified: 1831x601)
    'objects': '.main_pane.objects',    # Objects/signals panel (verified: 364x169)
    'processes': '.main_pane.process',  # Processes list (verified: 364x168)
    'sim': '.main_pane.structure',      # Structure/Instance hierarchy (verified: 364x320)
}


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
                                refresh_wave: bool = True,
                                zoom_range: Optional[tuple[str, str]] = None) -> Dict[str, Any]:
        """
        Quick workflow: recompile -> restart -> run -> refresh waveform

        Args:
            design_files: Design files (uses stored if None)
            testbench_file: Testbench file (uses stored if None)
            sim_time: Simulation time
            restart: Restart simulation after recompile (default: True)
            refresh_wave: Refresh waveform after run (default: True)
            zoom_range: Optional (start_time, end_time) tuple for custom zoom
                       e.g., ("1ms", "2ms") or None for full zoom

        Returns:
            Dictionary with results of each step

        Example:
            # Normal usage with full zoom
            controller.quick_recompile_and_run(sim_time="1us")

            # Custom zoom to specific range
            controller.quick_recompile_and_run(sim_time="3ms", zoom_range=("1ms", "2ms"))
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

            # Apply custom zoom if specified
            if zoom_range:
                start, end = zoom_range
                zoom_result = self.zoom_waveform_range(start, end)

                if not zoom_result.get('success'):
                    print(f"⚠ Zoom to {start}-{end} failed, using full zoom")
                    wave_result = self.client.refresh_waveform()
                else:
                    print(f"✓ Zoomed to range {start} - {end}")
                    # Also refresh to ensure waveform updates
                    wave_result = self.client.refresh_waveform()

                results["wave_refresh"] = wave_result
            else:
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

    def zoom_waveform_range(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """
        Zoom waveform to specific time range

        Args:
            start_time: Start time with unit (e.g., "0ns", "1us", "1.5ms")
            end_time: End time with unit (e.g., "100ns", "2us", "3ms")

        Returns:
            Response dictionary with success status

        Example:
            controller.zoom_waveform_range("1ms", "2ms")  # Zoom to 1ms-2ms range
            controller.zoom_waveform_range("0ns", "100ns")  # Zoom to first 100ns
        """
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}

        tcl_cmd = f"wave zoom range {start_time} {end_time}"
        return self.execute_tcl(tcl_cmd)

    def zoom_waveform_full(self) -> Dict[str, Any]:
        """
        Zoom waveform to show full simulation time

        Returns:
            Response dictionary with success status

        Example:
            controller.zoom_waveform_full()  # Return to full view
        """
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}

        return self.execute_tcl("wave zoom full")

    def find_pulse_times(self, signal_path: str = "Pulse", transcript: Optional[str] = None) -> List[int]:
        """
        Find pulse occurrence times from transcript display messages

        Args:
            signal_path: Signal name keyword to search for (default: "Pulse")
            transcript: Transcript content (reads from file if None)

        Returns:
            List of pulse times in nanoseconds

        Example:
            pulse_times = controller.find_pulse_times("Pulse")
            # Returns: [1005500000, 2005500000, 3005500000] for pulses at 1ms, 2ms, 3ms

            # Then zoom to first pulse with ±10us window:
            if pulse_times:
                t = pulse_times[0]
                controller.zoom_waveform_range(f"{t-10000}ns", f"{t+10000}ns")
        """
        if transcript is None:
            transcript = self.read_transcript()

        pulse_times = []

        # Search for time markers in display messages
        # Pattern: "[1005500000 ns] Pulse #1 detected"
        import re
        pattern = r"\[(\d+)\s+ns\].*" + re.escape(signal_path)

        for line in transcript.splitlines():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                time_ns = int(match.group(1))
                pulse_times.append(time_ns)

        return pulse_times

    def execute_tcl(self, tcl_code: str) -> Dict[str, Any]:
        """Execute arbitrary TCL command"""
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}
        return self.client.execute_tcl(tcl_code)

    def add_wave(self, signal_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Add signal(s) to waveform

        Args:
            signal_path: Signal path (e.g., "/counter_tb/dut/count")
                        If None, adds all top-level signals (add wave /*)

        Returns:
            Response dictionary with success status

        Example:
            # Add all top-level signals
            controller.add_wave()

            # Add specific signal
            controller.add_wave("/counter_tb/dut/count")

            # To change format, use change_wave_format()
            controller.change_wave_format("/counter_tb/dut/count", "unsigned")
        """
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}

        if signal_path is None:
            # Add all top-level signals
            tcl_cmd = "add wave /*"
        else:
            # Add specific signal
            tcl_cmd = f"add wave {signal_path}"

        return self.execute_tcl(tcl_cmd)

    def change_wave_format(self, signal_path: str, format: str) -> Dict[str, Any]:
        """
        Change display format of existing wave

        Args:
            signal_path: Signal path (e.g., "/counter_tb/dut/count" or "counter_tb/dut/count")
            format: New display format - "binary", "hex", "unsigned", "signed", "octal", "ascii"

        Returns:
            Response dictionary with success status

        Example:
            # Change counter to decimal
            controller.change_wave_format("/counter_tb/dut/count", "unsigned")

            # Change to hexadecimal
            controller.change_wave_format("/counter_tb/dut/state", "hex")

        Note:
            Uses ModelSim's property wave -radix command to change the display format
            of an existing signal. The signal name in the wave window is extracted
            from the full hierarchical path (uses the last component).
        """
        if not self.is_connected():
            return {"success": False, "message": "Not connected"}

        # Extract signal name from hierarchical path for wave window
        # Wave window uses the last component of the path
        signal_name = signal_path.split('/')[-1]

        # Use property wave -radix command to change format directly
        tcl_command = f"property wave -radix {format} {signal_name}"
        result = self.execute_tcl(tcl_command)

        # Refresh waveform to show the change
        if result.get('success', False):
            self.execute_tcl("wave refresh")

        return result

    @staticmethod
    def get_common_signal_formats() -> Dict[str, str]:
        """
        Return common signal format options for reference

        Returns:
            Dictionary of format names and descriptions

        Example:
            formats = ModelSimController.get_common_signal_formats()
            for name, desc in formats.items():
                print(f"{name}: {desc}")
        """
        return {
            "binary": "Binary (default) - 8'b00001010",
            "hex": "Hexadecimal - 8'h0A",
            "unsigned": "Unsigned decimal - 10",
            "signed": "Signed decimal - -6 or 10",
            "octal": "Octal - 8'o012",
            "ascii": "ASCII character - 'A'"
        }

    def capture_waveform_window(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Capture waveform window using Tcl geometry query

        This method queries ModelSim via Tcl socket to get the exact wave window
        position and size, then captures that specific area.

        Args:
            output_path: Path to save screenshot. If None, returns PIL Image only.

        Returns:
            Dictionary with:
            - success: bool
            - image: PIL.Image (if successful)
            - path: str (if saved)
            - geometry: str (e.g., "1200x600+100+50")
            - message: str

        Example:
            result = controller.capture_waveform_window(Path("wave.png"))
            if result['success']:
                print(f"Saved to {result['path']}")
                print(f"Geometry: {result['geometry']}")
        """
        if not self.is_connected():
            return {"success": False, "message": "Not connected to ModelSim"}

        try:
            import win32gui
            import win32ui
            import win32con
            from PIL import Image
            import re

            # Step 1: Get wave window geometry from Tcl
            geometry_result = self.client.get_wave_geometry()
            if not geometry_result.get('success'):
                return {
                    "success": False,
                    "message": f"Failed to get wave geometry: {geometry_result.get('message')}",
                    "errors": geometry_result.get('errors', [])
                }

            geometry_str = geometry_result.get('output', '').strip()
            if not geometry_str:
                return {
                    "success": False,
                    "message": "Empty geometry response from ModelSim"
                }

            # Step 2: Parse geometry string (format: WIDTHxHEIGHT+X+Y)
            match = re.match(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', geometry_str)
            if not match:
                return {
                    "success": False,
                    "message": f"Invalid geometry format: {geometry_str}"
                }

            width, height, x, y = map(int, match.groups())

            # Step 3: Find ModelSim window handle
            def find_modelsim_window():
                windows = []
                def callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if "ModelSim" in title:
                            windows.append((hwnd, title))
                    return True
                win32gui.EnumWindows(callback, None)
                return windows

            modelsim_windows = find_modelsim_window()
            if not modelsim_windows:
                return {
                    "success": False,
                    "message": "ModelSim window not found"
                }

            parent_hwnd = modelsim_windows[0][0]

            # Calculate client area offset
            # Tcl returns coordinates relative to parent window's client area
            # GetWindowDC uses coordinates relative to window (including title bar)
            client_x, client_y = win32gui.ClientToScreen(parent_hwnd, (0, 0))
            window_rect = win32gui.GetWindowRect(parent_hwnd)
            window_x, window_y = window_rect[0], window_rect[1]

            offset_x = client_x - window_x
            offset_y = client_y - window_y

            # Add offset to Tcl coordinates to get window coordinates
            capture_x = x + offset_x
            capture_y = y + offset_y

            # Step 4: Capture the specific region
            hwnd_dc = win32gui.GetWindowDC(parent_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # Copy wave window region (using window coordinates with offset)
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (capture_x, capture_y), win32con.SRCCOPY)

            # Convert to PIL Image
            bmp_info = bitmap.GetInfo()
            bmp_bits = bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_bits, 'raw', 'BGRX', 0, 1
            )

            # Clean up
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(parent_hwnd, hwnd_dc)

            # Step 5: Save if path provided
            result = {
                "success": True,
                "image": img,
                "geometry": geometry_str,
                "width": width,
                "height": height,
                "x": x,
                "y": y,
                "offset_x": offset_x,
                "offset_y": offset_y,
                "capture_x": capture_x,
                "capture_y": capture_y,
                "message": "Waveform window captured successfully"
            }

            if output_path:
                img.save(output_path)
                result["path"] = str(output_path.absolute())

            return result

        except ImportError as e:
            return {
                "success": False,
                "message": f"Missing required packages: {e}. Install with: pip install pywin32 pillow"
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "message": f"Screenshot failed: {e}",
                "traceback": traceback.format_exc()
            }

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

    # ============================================================
    # Screenshot Capture Methods
    # ============================================================

    def _find_modelsim_window(self) -> Optional[int]:
        """
        Find ModelSim parent window HWND

        Returns:
            Parent window HWND or None if not found
        """
        import win32gui

        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "ModelSim" in title:
                    windows.append(hwnd)
            return True

        win32gui.EnumWindows(callback, None)
        return windows[0] if windows else None

    def _get_panel_hwnd_via_tcl(self, widget_path: str) -> int:
        """
        Get panel HWND via Tcl winfo id command

        Args:
            widget_path: Tcl widget path (e.g., ".main_pane.wave")

        Returns:
            Window handle (HWND) as integer

        Raises:
            RuntimeError: If widget not found or Tcl command fails
        """
        if self.client is None or not self.client.is_connected():
            raise RuntimeError("Not connected to ModelSim. Call connect() first.")

        # Execute Tcl command to get window ID
        result = self.execute_tcl(f"winfo id {widget_path}")

        if not result.get('success'):
            raise RuntimeError(
                f"Failed to get HWND for {widget_path}: {result.get('message')}"
            )

        # Parse HWND from output (should be decimal integer or hex)
        try:
            hwnd_str = result['output'].strip()
            # Tcl returns in format like "0x12345" or decimal "74565"
            if hwnd_str.startswith('0x'):
                hwnd = int(hwnd_str, 16)
            else:
                hwnd = int(hwnd_str)
            return hwnd
        except (ValueError, KeyError) as e:
            raise RuntimeError(
                f"Failed to parse HWND from Tcl output '{result.get('output')}': {e}"
            )

    def _capture_window_by_hwnd(self, hwnd: int, output_path: Path) -> Dict[str, Any]:
        """
        Capture window by HWND using BitBlt

        Args:
            hwnd: Window handle to capture
            output_path: Where to save screenshot

        Returns:
            Dictionary with success, image, path, width, height
        """
        import win32gui
        import win32ui
        import win32con
        from PIL import Image

        try:
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Capture using BitBlt
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(bitmap)

            # Copy window contents
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

            # Convert to PIL Image
            bmp_info = bitmap.GetInfo()
            bmp_bits = bitmap.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmp_info['bmWidth'], bmp_info['bmHeight']),
                bmp_bits, 'raw', 'BGRX', 0, 1
            )

            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path)

            return {
                'success': True,
                'image': img,
                'path': str(output_path),
                'width': width,
                'height': height
            }

        finally:
            # Cleanup resources
            try:
                win32gui.DeleteObject(bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwnd_dc)
            except:
                pass  # Ignore cleanup errors

    def capture_screenshot(self, target: str = 'wave',
                          output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Capture screenshot of specified ModelSim panel

        Args:
            target: Panel to capture - 'modelsim', 'wave', 'objects',
                   'processes', 'transcript', 'sim'
            output_path: Optional custom path
                        (default: temp/modelsim_{target}.png)

        Returns:
            Dictionary with keys:
            - success: bool
            - image: PIL.Image
            - path: str
            - width: int
            - height: int
            - target: str
            - message: str

        Raises:
            ValueError: If target is invalid
            RuntimeError: If ModelSim or target window not found

        Example:
            # Capture waveform panel
            result = controller.capture_screenshot('wave')
            print(f"Saved to: {result['path']}")  # temp/modelsim_wave.png

            # Capture full window
            result = controller.capture_screenshot('modelsim')

            # Custom path
            result = controller.capture_screenshot(
                'wave', Path('custom/my_wave.png')
            )
        """
        # Validate target
        valid_targets = ['modelsim', 'wave', 'objects', 'processes',
                        'transcript', 'sim']
        if target not in valid_targets:
            raise ValueError(
                f"Invalid target: {target}. "
                f"Must be one of: {', '.join(valid_targets)}"
            )

        # Default output path
        if output_path is None:
            output_path = self.project_root / 'temp' / f'modelsim_{target}.png'

        # Find target window
        if target == 'modelsim':
            # Capture full parent window
            parent_hwnd = self._find_modelsim_window()
            if parent_hwnd is None:
                raise RuntimeError("ModelSim window not found. Is ModelSim running?")
            target_hwnd = parent_hwnd
        else:
            # Get panel HWND via Tcl winfo id command
            widget_path = PANEL_WIDGET_PATHS[target]
            target_hwnd = self._get_panel_hwnd_via_tcl(widget_path)

        # Capture
        result = self._capture_window_by_hwnd(target_hwnd, output_path)
        result['target'] = target
        result['message'] = f"Captured {target} panel to {result['path']}"

        return result


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
