"""
ModelSim Controller - Lean Infrastructure Layer
Provides minimal infrastructure for CLI scripts:
- Socket connection management
- TCL command execution
- Transcript file reading
- Common utilities (path normalization)

Author: Claude Code
Date: 2026-01-17
"""

import time
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from modelsim_client import ModelSimClient


class ModelSimController:
    """
    Lean controller for ModelSim automation with socket communication

    Provides essential infrastructure only:
    - Connection management (connect, disconnect, ping)
    - TCL command execution (execute_tcl)
    - File I/O (read_transcript)
    - Common utilities (normalize_path)
    """

    def __init__(self,
                 project_root: Path,
                 server_port: int = 12345):
        """
        Initialize ModelSim controller

        Args:
            project_root: Project root directory (e.g., Path("d:/Claude/HDL-DEV"))
            server_port: Socket server port (default: 12345)
        """
        self.project_root = Path(project_root)
        self.server_port = server_port

        # Initialize client (not connected yet)
        self.client: Optional[ModelSimClient] = None

    def connect(self, max_retries: int = 10, retry_delay: float = 1.0) -> bool:
        """
        Connect to ModelSim socket server

        Args:
            max_retries: Maximum connection attempts
            retry_delay: Delay between retries (seconds)

        Returns:
            True if connected successfully, False otherwise
        """
        self.client = ModelSimClient(port=self.server_port)

        for attempt in range(1, max_retries + 1):
            try:
                self.client.connect()
                return True
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect after {max_retries} attempts")
                    self.client = None
                    return False

        return False

    def disconnect(self):
        """Disconnect from ModelSim socket server"""
        if self.client and self.client.is_connected():
            self.client.disconnect()

    def is_connected(self) -> bool:
        """
        Check if connected to ModelSim socket server

        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and self.client.is_connected()

    def ping(self) -> bool:
        """
        Test socket server responsiveness

        Returns:
            True if server responds, False otherwise
        """
        if not self.is_connected():
            return False

        try:
            response = self.client.ping()
            return response.get('success', False)
        except Exception:
            return False

    def execute_tcl(self, tcl_code: str) -> Dict[str, Any]:
        """
        Execute TCL command in ModelSim

        Args:
            tcl_code: TCL command to execute

        Returns:
            Response dict with 'success' and 'result' keys
        """
        if not self.is_connected():
            return {
                'success': False,
                'message': 'Not connected to ModelSim'
            }

        try:
            return self.client.execute_tcl(tcl_code)
        except Exception as e:
            return {
                'success': False,
                'message': f'TCL execution failed: {e}'
            }

    def read_transcript(self, lines: Optional[int] = None) -> str:
        """
        Read ModelSim transcript file

        Args:
            lines: Number of lines to read (None = all)

        Returns:
            Transcript content as string
        """
        transcript_file = self.project_root / "sim" / "transcript"

        if not transcript_file.exists():
            return ""

        try:
            with open(transcript_file, 'r', encoding='utf-8', errors='ignore') as f:
                if lines is None:
                    return f.read()
                else:
                    all_lines = f.readlines()
                    return ''.join(all_lines[-lines:])
        except Exception as e:
            print(f"Error reading transcript: {e}")
            return ""

    def normalize_path(self, path: str) -> str:
        """
        Normalize path for ModelSim (Windows backslashes → forward slashes, add ../ prefix)

        Args:
            path: File path (can contain backslashes)

        Returns:
            Path with forward slashes and ../ prefix (relative to sim/ directory)

        Example:
            >>> controller.normalize_path("hdl\\design\\counter.v")
            "../hdl/design/counter.v"
            >>> controller.normalize_path("../hdl/design/counter.v")
            "../hdl/design/counter.v"
        """
        # Convert backslashes to forward slashes
        normalized = str(Path(path)).replace("\\", "/")

        # Add ../ prefix if path doesn't already start with it
        # (ModelSim runs from sim/ directory, so paths need to be relative to sim/)
        if not normalized.startswith(".."):
            normalized = f"../{normalized}"

        return normalized

    def refresh_waveform(self) -> Dict[str, Any]:
        """
        Refresh waveform display and bring wave window to front

        This is a common utility used by multiple scripts (load_module, run_sim, refresh_waveform).
        Executes: wave zoom full + view wave + raise .main_pane.wave

        Returns:
            Response dictionary with success status
        """
        if not self.is_connected():
            return {
                "success": False,
                "message": "Not connected to ModelSim server"
            }

        # Zoom to full range
        zoom_result = self.execute_tcl("wave zoom full")

        # Bring wave window to front
        self.execute_tcl("view wave")
        self.execute_tcl("raise .main_pane.wave")

        return zoom_result

    def print_response(self, response: Dict[str, Any]):
        """
        Pretty-print server response

        Args:
            response: Response dict from execute_tcl() or other methods
        """
        if response.get('success'):
            print("✓ Success")
            if 'result' in response and response['result']:
                print(f"Result: {response['result']}")
        else:
            print("✗ Failed")
            if 'message' in response:
                print(f"Error: {response['message']}")

    def shutdown_server(self):
        """Shutdown ModelSim socket server (keeps GUI open)"""
        if not self.is_connected():
            print("Not connected to server")
            return

        try:
            self.client.shutdown()
            self.disconnect()
            print("Server shutdown successfully")
        except Exception as e:
            print(f"Failed to shutdown server: {e}")
