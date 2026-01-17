#!/usr/bin/env python3
"""
Read ModelSim transcript (simulation log).

This script reads the transcript file directly without needing ModelSim connection.
"""

import sys
from pathlib import Path


def highlight_line(line):
    """Add color/emphasis to important lines."""
    line_lower = line.lower()

    if 'test_result:' in line_lower:
        if 'pass' in line_lower:
            return f"✓ {line}"
        elif 'fail' in line_lower:
            return f"✗ {line}"
    elif '** error' in line_lower:
        return f"✗ {line}"
    elif '** warning' in line_lower:
        return f"⚠ {line}"

    return line


def main():
    """Main entry point for get_transcript CLI script."""
    lines_to_show = 50  # Default

    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print("Usage: get_transcript.py [lines]")
            print()
            print("Reads ModelSim transcript file.")
            print()
            print("Arguments:")
            print("  lines  - Number of lines to show (default: 50)")
            print("          Use 'all' to show entire file")
            print()
            print("Examples:")
            print('  python get_transcript.py        # Last 50 lines')
            print('  python get_transcript.py 100    # Last 100 lines')
            print('  python get_transcript.py all    # Entire file')
            sys.exit(0)

        arg = sys.argv[1].lower()
        if arg == 'all':
            lines_to_show = None  # Show all
        else:
            try:
                lines_to_show = int(arg)
                if lines_to_show <= 0:
                    print("✗ ERROR: lines must be positive")
                    sys.exit(1)
            except ValueError:
                print(f"✗ ERROR: Invalid argument '{sys.argv[1]}'")
                print("  Expected: number or 'all'")
                sys.exit(1)

    # Get project root from current working directory
    project_root = Path.cwd()
    transcript_file = project_root / "sim" / "transcript"

    # Check if file exists
    if not transcript_file.exists():
        print("✗ ERROR: Transcript file not found")
        print(f"  Expected: {transcript_file}")
        print()
        print("Make sure:")
        print("  1. You are in the project root directory")
        print("  2. ModelSim has been run at least once")
        sys.exit(1)

    try:
        # Read transcript
        with open(transcript_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()

        if not all_lines:
            print("✗ Transcript file is empty")
            sys.exit(0)

        # Get lines to display
        if lines_to_show is None:
            lines = all_lines
            print(f"=" * 60)
            print(f"ModelSim Transcript (all {len(all_lines)} lines)")
            print(f"=" * 60)
        else:
            lines = all_lines[-lines_to_show:]
            print(f"=" * 60)
            print(f"ModelSim Transcript (last {len(lines)} lines)")
            print(f"=" * 60)

        print()

        # Display with highlighting
        for line in lines:
            line = line.rstrip()
            highlighted = highlight_line(line)
            print(highlighted)

        print()
        print(f"=" * 60)
        print(f"Total lines in file: {len(all_lines)}")
        print(f"=" * 60)

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
