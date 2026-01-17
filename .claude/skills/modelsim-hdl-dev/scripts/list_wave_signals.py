#!/usr/bin/env python3
"""
List signals currently displayed in wave window.

This script exports wave configuration and parses it to show signal names and formats.
"""

import sys
import re
import tempfile
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def parse_wave_format_file(file_path):
    """
    Parse ModelSim wave format file to extract signal names and formats.

    Returns:
        list: List of (signal_name, format) tuples
    """
    signals = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Pattern for signal lines: add wave -noupdate -radix <format> <signal_path>
        # or: add wave -noupdate <signal_path>
        pattern = r'add wave.*?(?:-radix (\w+)\s+)?(/[\w/]+)'

        matches = re.findall(pattern, content)

        for radix, signal_path in matches:
            format_str = radix if radix else 'default'
            signals.append((signal_path, format_str))

    except Exception as e:
        print(f"Warning: Could not parse wave format file: {e}")

    return signals


def main():
    """Main entry point for list_wave_signals CLI script."""
    verbose = False

    if len(sys.argv) > 1:
        if sys.argv[1] in ['--verbose', '-v']:
            verbose = True
        elif sys.argv[1] in ['--help', '-h']:
            print("Usage: list_wave_signals.py [--verbose]")
            print()
            print("Lists signals currently displayed in the wave window.")
            print()
            print("Options:")
            print("  --verbose, -v  Show signal formats (radix)")
            print()
            print("Examples:")
            print('  python list_wave_signals.py')
            print('  python list_wave_signals.py --verbose')
            sys.exit(0)
        else:
            print("✗ ERROR: Invalid argument")
            print('Use --help for usage information')
            sys.exit(1)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Listing signals in wave window...")
    print()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            sys.exit(1)

        # Create temporary file for wave export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.do', delete=False) as tmp:
            temp_file = Path(tmp.name)

        # Export wave configuration
        # Convert Windows path to forward slashes for TCL
        temp_file_tcl = str(temp_file).replace('\\', '/')

        # Use the correct command as suggested by user
        tcl_cmd = f'write format wave {temp_file_tcl}'
        result = controller.execute_tcl(tcl_cmd)

        # Disconnect
        controller.disconnect()

        if not result['success']:
            print("✗ FAILED: Could not export wave configuration")
            print(f"  {result.get('message', 'Unknown error')}")
            temp_file.unlink(missing_ok=True)
            sys.exit(1)

        # Parse the exported file
        signals = parse_wave_format_file(temp_file)

        # Clean up temp file
        temp_file.unlink(missing_ok=True)

        # Display results
        if not signals:
            print("No signals found in wave window")
            print()
            print("Tip: Add signals with add_wave.py")
            sys.exit(0)

        print("=" * 60)
        print(f"Signals in Wave Window ({len(signals)} total)")
        print("=" * 60)
        print()

        for idx, (signal_path, format_str) in enumerate(signals, 1):
            if verbose and format_str != 'default':
                print(f"{idx}. {signal_path} [{format_str}]")
            else:
                print(f"{idx}. {signal_path}")

        print()
        print("=" * 60)

        if not verbose:
            print()
            print("Tip: Use --verbose to show signal formats")

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
