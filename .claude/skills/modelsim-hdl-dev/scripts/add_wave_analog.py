#!/usr/bin/env python3
"""
Add signal to waveform with analog display and auto-calculated min/max scale.

This script:
1. Gets signal type information using ModelSim's describe command
2. Extracts bit width from [N:M] pattern (Register, Wire, etc.)
3. Calculates min/max scale based on bit width and radix (signed/unsigned)
4. Adds signal with proper analog format and scale

Only signals with explicit bit width patterns are supported.
Integer and Real types are rejected due to unknown value ranges.
"""

import sys
import re
from pathlib import Path

# Import from same directory
sys.path.insert(0, str(Path(__file__).parent / "internal"))
from modelsim_controller import ModelSimController


def parse_bit_width(desc_output):
    """
    Parse describe output to extract bit width from [N:M] pattern.

    Args:
        desc_output: Output from ModelSim describe command

    Returns:
        int: Number of bits, or None if no [N:M] pattern found

    Examples:
        "Register [7:0]" → 8
        "Wire [15:0]" → 16
        "Wire signed [11:0]" → 12
        "[0:7]" → 8 (handles reverse order with abs())
        "Integer" → None
        "Real" → None
    """
    # Search for [N:M] pattern anywhere in the output
    match = re.search(r'\[(\d+):(\d+)\]', desc_output)

    if not match:
        return None

    # Extract N and M
    n = int(match.group(1))
    m = int(match.group(2))

    # Calculate bit width using abs() to handle both [7:0] and [0:7]
    bits = abs(n - m) + 1

    return bits


def calculate_scale(bits, radix):
    """
    Calculate min/max scale from bit width and radix.

    Args:
        bits: Number of bits (e.g., 8, 16, 32)
        radix: "signed" or "unsigned"

    Returns:
        tuple: (min_value, max_value)

    Examples:
        (8, "unsigned") → (0, 255)
        (8, "signed") → (-128, 127)
        (12, "unsigned") → (0, 4095)
        (12, "signed") → (-2048, 2047)
    """
    if radix == "unsigned":
        min_val = 0
        max_val = (2 ** bits) - 1
    else:  # signed
        min_val = -(2 ** (bits - 1))
        max_val = (2 ** (bits - 1)) - 1

    return min_val, max_val


def extract_signal_name(signal_path):
    """
    Extract signal name from hierarchical path.

    Args:
        signal_path: Full signal path (e.g., "counter_tb/dut/count")

    Returns:
        str: Last component of path

    Examples:
        "counter_tb/dut/count" → "count"
        "/pwm_tb/duty" → "duty"
        "counter" → "counter"
    """
    # Remove leading slash if present
    path = signal_path.lstrip('/')

    # Split by / and get last component
    components = path.split('/')
    signal_name = components[-1]

    return signal_name


def main():
    """Main entry point for add_wave_analog CLI script."""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        print("Usage: add_wave_analog.py <signal_path> --radix <signed|unsigned> [--height <pixels>]")
        print()
        print("Add signal to waveform with analog display and auto-calculated scale.")
        print()
        print("Arguments:")
        print("  signal_path  - Full hierarchical signal path (e.g., 'counter_tb/count')")
        print("  --radix      - REQUIRED: 'signed' or 'unsigned'")
        print("  --height     - Optional: Display height in pixels (default: 80)")
        print()
        print("IMPORTANT: Signal path must NOT start with '/' (Git Bash issue)")
        print()
        print("Examples:")
        print('  python add_wave_analog.py "counter_tb/count" --radix unsigned')
        print('  python add_wave_analog.py "adc_tb/sample" --radix signed --height 120')
        print()
        print("Supported signal types:")
        print("  - Register [N:M] (e.g., Register [7:0])")
        print("  - Wire [N:M] (e.g., Wire [15:0])")
        print("  - Any type with explicit bit width pattern [N:M]")
        print()
        print("NOT supported:")
        print("  - Integer (no bit width specification)")
        print("  - Real (inappropriate for analog display)")
        print()
        print("Note: Signal is added with '_analog' suffix label to avoid conflicts")
        sys.exit(0 if len(sys.argv) == 1 else 1)

    # Parse arguments
    signal_path = sys.argv[1]

    # Parse optional arguments
    radix = None
    height = 80  # default

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--radix':
            if i + 1 >= len(sys.argv):
                print("✗ ERROR: --radix requires a value")
                sys.exit(1)
            radix = sys.argv[i + 1].lower()  # Normalize case
            i += 2
        elif sys.argv[i] == '--height':
            if i + 1 >= len(sys.argv):
                print("✗ ERROR: --height requires a value")
                sys.exit(1)
            try:
                height = int(sys.argv[i + 1])
                if height <= 0:
                    print("✗ ERROR: Height must be a positive integer")
                    sys.exit(1)
            except ValueError:
                print(f"✗ ERROR: Invalid height value '{sys.argv[i + 1]}' (must be integer)")
                sys.exit(1)
            i += 2
        else:
            print(f"✗ ERROR: Unknown argument '{sys.argv[i]}'")
            sys.exit(1)

    # Validate radix (REQUIRED)
    if radix is None:
        print("✗ ERROR: Radix (signed/unsigned) is required for analog display")
        print("  Use: --radix signed  or  --radix unsigned")
        sys.exit(1)

    if radix not in ['signed', 'unsigned']:
        print(f"✗ ERROR: Invalid radix '{radix}'. Must be 'signed' or 'unsigned'")
        sys.exit(1)

    # Get project root from current working directory
    project_root = Path.cwd()

    print("⏳ Adding analog waveform...")
    print(f"  Signal: {signal_path}")
    print(f"  Radix: {radix}")
    print(f"  Height: {height} pixels")
    print()

    try:
        # Create controller
        controller = ModelSimController(project_root)

        # Connect to ModelSim
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot connect to ModelSim socket server")
            print("  Make sure ModelSim is running with: python scripts/start_modelsim_server.py")
            sys.exit(1)

        print("Connected to ModelSim at localhost:12345")

        # Ensure signal path starts with / for describe command
        full_path = signal_path if signal_path.startswith('/') else f"/{signal_path}"

        # Step 1: Get signal type using describe command
        # Use echo to capture output (based on manual testing)
        describe_cmd = f'set desc [describe {full_path}]; echo $desc'
        result = controller.execute_tcl(describe_cmd)

        # Disconnect
        controller.disconnect()
        print("Disconnected from ModelSim")
        print()

        # Check if describe command succeeded
        if not result['success']:
            print("✗ ERROR: Failed to get signal type information")
            error_msg = controller.analyze_error(result, context="waveform")
            print(error_msg)
            print()
            print("Possible causes:")
            print("  - Signal does not exist")
            print("  - Signal path is incorrect")
            print("  - No simulation loaded")
            sys.exit(1)

        # Extract describe output from transcript
        # The controller reads transcript, so we need to check the most recent output
        transcript = controller.read_transcript(lines=10)

        # Parse describe output from transcript
        # Look for the echo output (should be after "echo $desc" line)
        desc_output = None
        lines = transcript.strip().split('\n')
        for i, line in enumerate(lines):
            if 'echo $desc' in line or 'echo \\$desc' in line:
                # Next line should be the describe output
                if i + 1 < len(lines):
                    desc_output = lines[i + 1].strip()
                    # Remove leading '#' if present (transcript format)
                    if desc_output.startswith('#'):
                        desc_output = desc_output[1:].strip()
                    break

        if not desc_output:
            print("✗ ERROR: Could not extract signal type information")
            print("  Transcript output:")
            print(transcript)
            sys.exit(1)

        print(f"Signal type: {desc_output}")

        # Step 2: Parse bit width
        bits = parse_bit_width(desc_output)

        if bits is None:
            print()
            print(f"✗ ERROR: Signal type '{desc_output}' not supported for analog display")
            print("  No bit width [N:M] pattern found")
            print()
            print("Supported types:")
            print("  - Register [N:M]")
            print("  - Wire [N:M]")
            print("  - Any type with explicit bit width specification")
            print()
            print("NOT supported:")
            print("  - Integer (use digital display instead)")
            print("  - Real (use digital display instead)")
            sys.exit(1)

        print(f"Bit width: {bits} bits")

        # Step 3: Calculate min/max scale
        min_val, max_val = calculate_scale(bits, radix)
        print(f"Scale: min={min_val}, max={max_val} ({radix})")

        # Step 4: Extract signal name and generate label
        signal_name = extract_signal_name(signal_path)
        label = f"{signal_name}_analog"
        print(f"Label: {label}")
        print()

        # Step 5: Build add wave command with label
        add_wave_cmd = (
            f"add wave -label {label} "
            f"-format Analog-Step "
            f"-height {height} "
            f"-min {min_val} "
            f"-max {max_val} "
            f"-radix {radix} "
            f"{full_path}"
        )

        print(f"Executing: {add_wave_cmd}")
        print()

        # Reconnect to execute add wave
        if not controller.connect(max_retries=3, retry_delay=0.5):
            print("✗ ERROR: Cannot reconnect to ModelSim")
            sys.exit(1)

        result = controller.execute_tcl(add_wave_cmd)
        controller.disconnect()

        if not result['success']:
            print("✗ ERROR: Failed to add waveform")
            error_msg = controller.analyze_error(result, context="waveform")
            print(error_msg)
            sys.exit(1)

        print("✓ SUCCESS: Analog waveform added!")
        print(f"  Signal: {full_path}")
        print(f"  Label: {label}")
        print(f"  Scale: {min_val} to {max_val} ({radix})")
        print(f"  Height: {height} pixels")
        print()
        print("Note: Signal appears as '{label}' in wave window")
        print("      This allows both digital and analog views of same signal")

        sys.exit(0)

    except KeyboardInterrupt:
        print()
        print("✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
