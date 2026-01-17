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
from typing import Optional, Dict, Any, List

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

    def analyze_error(self, result: Dict[str, Any], context: str = "") -> str:
        """
        Analyze error response and generate user-friendly error message

        This is a common utility used by all CLI scripts for better error reporting.
        Extracts ModelSim error codes, file paths, line numbers, and provides
        context-specific suggestions.

        Args:
            result: Response dict from execute_tcl() with keys:
                   - success: bool
                   - message: str
                   - output: str (raw ModelSim output)
                   - errors: List[str]
                   - warnings: List[str]
            context: Context hint for suggestions:
                    - "compilation" - vlog errors
                    - "simulation" - vsim errors
                    - "waveform" - wave command errors
                    - "" (empty) - generic

        Returns:
            Formatted error message string with:
            - What went wrong (summary)
            - Where it happened (file, line if available)
            - Why it happened (error code and message)
            - How to fix it (context-specific suggestions)
        """
        if result.get('success'):
            return ""  # No error

        message_parts = []

        # 1. Extract basic error info from result dict
        # Normalize message field (can be string or list)
        message_raw = result.get('message', 'Unknown error')
        if isinstance(message_raw, list):
            error_msg = ' '.join(str(m) for m in message_raw)
        else:
            error_msg = str(message_raw)

        # Normalize output field (can be string or list)
        output_raw = result.get('output', '')
        if isinstance(output_raw, list):
            output = ' '.join(str(o) for o in output_raw)
        else:
            output = str(output_raw) if output_raw else ''

        # Normalize errors field (can be list or string)
        errors_raw = result.get('errors', [])
        if isinstance(errors_raw, str):
            # If errors is a string, wrap it in a list
            errors = [errors_raw] if errors_raw else []
        elif isinstance(errors_raw, list):
            errors = errors_raw
        else:
            errors = []

        # 2. Parse ModelSim error patterns to extract structured details
        error_details = self._parse_modelsim_error(output, errors)

        # 3. Build formatted error message
        message_parts.append("=" * 60)
        message_parts.append(f"ERROR: {error_details['summary']}")
        message_parts.append("=" * 60)

        # Add file/line info if available
        if error_details['file']:
            message_parts.append(f"  File: {error_details['file']}")
        if error_details['line']:
            message_parts.append(f"  Line: {error_details['line']}")

        # Add error code if available
        if error_details['error_code']:
            message_parts.append(f"  Code: {error_details['error_code']}")

        # Add errno if available (for file access errors)
        if error_details.get('errno'):
            message_parts.append(f"  Errno: {error_details['errno']}")

        # Add detailed error message
        message_parts.append(f"\n  {error_details['message']}")

        # Add context-specific suggestions
        suggestions = self._get_error_suggestions(
            error_details['error_code'],
            error_details['message'],
            context
        )

        if suggestions:
            message_parts.append("\nSuggestions:")
            for suggestion in suggestions:
                message_parts.append(f"  • {suggestion}")

        message_parts.append("=" * 60)

        return "\n".join(message_parts)

    def _parse_modelsim_error(self, output: str, errors: List[str]) -> Dict[str, str]:
        """
        Parse ModelSim error text to extract structured information

        Recognizes common ModelSim error patterns and extracts:
        - Error code (vlog-XXXX, vsim-XXXX)
        - File path and line number (when present)
        - Error message text
        - errno codes (for file errors)

        Patterns based on real errors found in sim/transcript:
        - vlog-7: File open failures with errno
        - vlog-2054: Invalid file specification
        - vlog-13069: Syntax errors with file and line
        - vsim-4005: Invalid command arguments

        Args:
            output: Raw error text from ModelSim
            errors: Error list from TCL server response

        Returns:
            Dictionary with keys: file, line, error_code, message, summary, errno
        """
        import re

        result = {
            'file': '',
            'line': '',
            'error_code': '',
            'message': '',
            'summary': 'Operation failed',
            'errno': ''
        }

        # Pattern 1: ** Error: (vlog-13069) file.v(15): message
        # Example: ** Error: (vlog-13069) counter.v(42): near "endmodule": syntax error
        pattern1 = r'\*\* Error: \(([^)]+)\) ([^(]+)\((\d+)\): (.+)'
        match = re.search(pattern1, output)
        if match:
            result['error_code'] = match.group(1)
            result['file'] = match.group(2).strip()
            result['line'] = match.group(3)
            result['message'] = match.group(4)
            result['summary'] = f"Compilation error in {result['file']}"
            return result

        # Pattern 2: ** Error: (vlog-7) Failed to open ... (errno = ENOENT)
        # Example: ** Error: (vlog-7) Failed to open design unit file "file.v" in read mode.\nNo such file or directory. (errno = ENOENT)
        pattern2 = r'\*\* Error: \(([^)]+)\) (.+?)\(errno = (\w+)\)'
        match = re.search(pattern2, output, re.DOTALL)
        if match:
            result['error_code'] = match.group(1)
            result['message'] = match.group(2).strip()
            result['errno'] = match.group(3)
            result['summary'] = "File access error"
            return result

        # Pattern 3: ** Error: (vlog-2054) File "..." is a directory
        # Generic pattern for other error codes
        pattern3 = r'\*\* Error: \(([^)]+)\) (.+)'
        match = re.search(pattern3, output)
        if match:
            result['error_code'] = match.group(1)
            result['message'] = match.group(2)
            # Categorize by error code prefix
            if 'vlog' in match.group(1):
                result['summary'] = "Compilation error"
            elif 'vsim' in match.group(1):
                result['summary'] = "Simulation error"
            else:
                result['summary'] = "ModelSim error"
            return result

        # Pattern 4: Generic error from errors list (no error code)
        if errors:
            result['message'] = errors[0]
            result['summary'] = "Command failed"
        elif output:
            result['message'] = output
            result['summary'] = "Command failed"

        return result

    def _get_error_suggestions(self, error_code: str, message: str, context: str) -> List[str]:
        """
        Get actionable suggestions based on error code, message, and context

        Uses knowledge from:
        - Real error examples found in transcript
        - troubleshooting.md documentation
        - Common HDL development issues

        Args:
            error_code: ModelSim error code (e.g., "vlog-7", "vsim-4005")
            message: Error message text
            context: Context hint ("compilation", "simulation", "waveform", "")

        Returns:
            List of actionable suggestion strings
        """
        suggestions = []

        # Specific error code handling (based on real examples from transcript)
        if error_code == 'vlog-7':
            suggestions.extend([
                "File not found - Check path is relative from sim/ directory",
                "Use '../hdl/design/file.v' not 'hdl/design/file.v'",
                "Verify file exists and spelling is correct"
            ])
            return suggestions

        elif error_code == 'vlog-2054':
            suggestions.extend([
                "File specification is invalid (possibly a directory)",
                "Check for backslash vs forward slash issues",
                "Ensure you're specifying a .v file, not a directory"
            ])
            return suggestions

        elif error_code == 'vsim-4005':
            suggestions.extend([
                "Invalid command argument provided",
                "Check ModelSim command syntax",
                "Use --help flag for correct usage"
            ])
            return suggestions

        # Generic compilation errors (vlog-*)
        if error_code.startswith('vlog'):
            if 'syntax error' in message.lower():
                suggestions.extend([
                    "Check for missing semicolons",
                    "Verify begin/end blocks are properly closed",
                    "Check for mismatched parentheses or brackets"
                ])
            elif 'not found' in message.lower() or 'cannot find' in message.lower() or 'failed to open' in message.lower():
                suggestions.extend([
                    "Verify file path is relative from sim/ directory (use ../hdl/)",
                    "Use forward slashes in paths, not backslashes",
                    "Check that file exists and spelling is correct"
                ])
            elif 'undeclared' in message.lower():
                suggestions.extend([
                    "Check signal/variable declarations",
                    "Verify signal is declared before use",
                    "Check spelling of signal name"
                ])

        # Simulation errors (vsim-*)
        elif error_code.startswith('vsim'):
            if 'not found' in message.lower() or 'unable to find' in message.lower():
                suggestions.extend([
                    "Check if design was compiled successfully",
                    "Verify module name is correct",
                    "Try running: vlib work && vlog <files>"
                ])

        # Waveform errors (context-based)
        if context == "waveform":
            if 'not found' in message.lower() or 'invalid' in message.lower():
                suggestions.extend([
                    "Run list_wave_signals.py to get exact signal names",
                    "Do not use leading '/' in signal paths (Git Bash issue)",
                    "Check signal path format: 'module/signal' not '/module/signal'"
                ])
            if 'radix' in message.lower() or 'property wave' in message.lower():
                suggestions.extend([
                    "Valid formats: binary, hex, unsigned, signed, octal, ascii",
                    "Use list_wave_signals.py first to confirm signal exists"
                ])

        # Generic suggestions based on context (fallback)
        if not suggestions:
            if context == "compilation":
                suggestions.extend([
                    "For detailed error messages, run: python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50",
                    "Or check sim/transcript file directly"
                ])
            elif context == "simulation":
                suggestions.extend([
                    "For detailed output, run: python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50",
                    "Or check sim/transcript file directly"
                ])
            else:
                suggestions.extend([
                    "For more details, run: python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50",
                    "Or check ModelSim transcript window"
                ])

        return suggestions

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
