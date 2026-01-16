"""
ModelSim Socket Client
Connects to a running ModelSim instance with socket server and sends commands
Author: Claude Code
Date: 2026-01-14
"""

import socket
import json
import time
from typing import Dict, List, Optional, Any


class ModelSimClient:
    """Client for communicating with ModelSim via TCP socket"""

    def __init__(self, host: str = "localhost", port: int = 12345, timeout: float = 30.0):
        """
        Initialize ModelSim client

        Args:
            host: Server hostname (default: localhost)
            port: Server port (default: 12345)
            timeout: Socket timeout in seconds (default: 30.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self._connected = False

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def connect(self, max_retries: int = 10, retry_delay: float = 1.0) -> bool:
        """
        Connect to ModelSim socket server with retry logic

        Args:
            max_retries: Maximum number of connection attempts (default: 10)
            retry_delay: Delay between retries in seconds (default: 1.0)

        Returns:
            True if connected successfully, False otherwise
        """
        if self._connected:
            print("Already connected")
            return True

        for attempt in range(max_retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)
                self.socket.connect((self.host, self.port))
                self._connected = True
                print(f"Connected to ModelSim at {self.host}:{self.port}")
                return True

            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to connect after {max_retries} attempts")
                    print("Make sure ModelSim is running with socket server enabled")
                    return False

        return False

    def disconnect(self):
        """Disconnect from ModelSim socket server"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
            finally:
                self.socket = None
                self._connected = False
                print("Disconnected from ModelSim")

    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self._connected

    def send_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send command to ModelSim and receive response

        Args:
            command: Command name (ping, recompile, restart, run, wave_refresh, exec_tcl, shutdown)
            params: Command parameters as dictionary

        Returns:
            Response dictionary with keys: success, message, output, errors, warnings

        Raises:
            ConnectionError: If not connected to server
            TimeoutError: If server doesn't respond within timeout
        """
        if not self._connected or not self.socket:
            raise ConnectionError("Not connected to ModelSim server")

        if params is None:
            params = {}

        # Create command message
        message = {
            "command": command,
            "params": params
        }

        try:
            # Send command as JSON
            json_str = json.dumps(message)
            self.socket.sendall((json_str + "\n").encode('utf-8'))

            # Receive response
            response_data = b""
            while True:
                chunk = self.socket.recv(4096)
                if not chunk:
                    raise ConnectionError("Server closed connection")
                response_data += chunk
                if b"\n" in response_data:
                    break

            # Parse JSON response
            response_str = response_data.decode('utf-8').strip()
            response = json.loads(response_str)

            return response

        except socket.timeout:
            raise TimeoutError(f"Command '{command}' timed out after {self.timeout} seconds")
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"Failed to parse server response: {e}",
                "output": response_data.decode('utf-8', errors='ignore'),
                "errors": [f"JSON decode error: {e}"],
                "warnings": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Communication error: {e}",
                "output": "",
                "errors": [str(e)],
                "warnings": []
            }

    def ping(self) -> bool:
        """
        Ping server to check if it's alive

        Returns:
            True if server responds, False otherwise
        """
        try:
            response = self.send_command("ping")
            return response.get("success", False)
        except Exception as e:
            print(f"Ping failed: {e}")
            return False

    def recompile(self, design_files: List[str], testbench_file: str = "") -> Dict[str, Any]:
        """
        Recompile design and testbench files

        Args:
            design_files: List of design file paths
            testbench_file: Testbench file path (optional)

        Returns:
            Response dictionary with compilation results
        """
        params = {
            "design_files": design_files
        }
        if testbench_file:
            params["testbench_file"] = testbench_file

        return self.send_command("recompile", params)

    def restart_simulation(self) -> Dict[str, Any]:
        """
        Restart simulation (restart -f)

        Returns:
            Response dictionary
        """
        return self.send_command("restart")

    def run_simulation(self, time: str) -> Dict[str, Any]:
        """
        Run simulation for specified time

        Args:
            time: Simulation time (e.g., "1us", "100ns", "10ms")

        Returns:
            Response dictionary
        """
        params = {"time": time}
        return self.send_command("run", params)

    def refresh_waveform(self) -> Dict[str, Any]:
        """
        Refresh waveform display (zoom full and bring to front)

        Returns:
            Response dictionary
        """
        return self.send_command("wave_refresh")

    def execute_tcl(self, tcl_code: str) -> Dict[str, Any]:
        """
        Execute arbitrary TCL command in ModelSim

        Args:
            tcl_code: TCL command to execute

        Returns:
            Response dictionary with command output
        """
        params = {"tcl_code": tcl_code}
        return self.send_command("exec_tcl", params)

    def get_wave_geometry(self) -> Dict[str, Any]:
        """
        Get wave window geometry from ModelSim

        Returns:
            Response dictionary with geometry string (e.g., "1200x600+100+50")
            Format: WIDTHxHEIGHT+X+Y
        """
        return self.send_command("get_wave_geometry")

    def shutdown_server(self) -> Dict[str, Any]:
        """
        Shutdown socket server (ModelSim continues running)

        Returns:
            Response dictionary
        """
        response = self.send_command("shutdown")
        self._connected = False
        return response

    def print_response(self, response: Dict[str, Any]):
        """
        Pretty print response from server

        Args:
            response: Response dictionary
        """
        if response.get("success"):
            print(f"✓ SUCCESS: {response.get('message', 'Command completed')}")
        else:
            print(f"✗ FAILED: {response.get('message', 'Command failed')}")

        # Print output
        output = response.get("output", "")
        if output:
            print(f"\nOutput:\n{output}")

        # Print errors
        errors = response.get("errors", [])
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")

        # Print warnings
        warnings = response.get("warnings", [])
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")


def main():
    """Example usage"""
    # Connect to ModelSim
    client = ModelSimClient()

    if not client.connect():
        print("Failed to connect to ModelSim")
        print("Make sure ModelSim is running with socket server enabled:")
        print("  1. Start ModelSim GUI")
        print("  2. In Transcript: source scripts/modelsim_socket_server.tcl")
        print("  3. In Transcript: start_socket_server 12345")
        return

    try:
        # Test ping
        print("\n" + "="*50)
        print("Testing ping...")
        if client.ping():
            print("✓ Ping successful")
        else:
            print("✗ Ping failed")

        # Example: Recompile
        print("\n" + "="*50)
        print("Example: Recompiling design...")
        response = client.recompile(
            design_files=["d:/Claude/Ralph_loop/hdl/design/counter.v"],
            testbench_file="d:/Claude/Ralph_loop/hdl/testbench/counter_tb.v"
        )
        client.print_response(response)

        if response['success']:
            # Restart simulation
            print("\n" + "="*50)
            print("Restarting simulation...")
            response = client.restart_simulation()
            client.print_response(response)

            # Run simulation
            print("\n" + "="*50)
            print("Running simulation...")
            response = client.run_simulation("1us")
            client.print_response(response)

            # Refresh waveform
            print("\n" + "="*50)
            print("Refreshing waveform...")
            response = client.refresh_waveform()
            client.print_response(response)

        # Example: Execute TCL command
        print("\n" + "="*50)
        print("Example: Execute TCL command...")
        response = client.execute_tcl("pwd")
        client.print_response(response)

    finally:
        # Disconnect
        client.disconnect()


if __name__ == "__main__":
    main()
