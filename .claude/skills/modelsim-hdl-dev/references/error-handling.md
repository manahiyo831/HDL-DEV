# Error Handling Reference

All CLI scripts provide detailed, user-friendly error messages with automatic analysis of ModelSim errors.

## Error Message Structure

When an error occurs, you'll see:

- **What went wrong** - Clear error summary (e.g., "Compilation error in hdl/design/counter.v")
- **Where it happened** - File path and line number (extracted from ModelSim output)
- **Why it happened** - Error code (e.g., vlog-13069, vsim-4005) and detailed message
- **How to fix** - Context-specific suggestions based on error type

## Example Error Outputs

### Compilation Error

```
============================================================
ERROR: Compilation error in hdl/design/counter.v
============================================================
  File: hdl/design/counter.v
  Line: 15
  Code: vlog-13069

  near "endmodule": syntax error, unexpected endmodule.

Suggestions:
  • Check for missing semicolons
  • Verify begin/end blocks are properly closed
  • Check for mismatched parentheses or brackets
============================================================
```

### File Not Found Error

```
============================================================
ERROR: File access error
============================================================
  Code: vlog-7
  Errno: ENOENT

  Failed to open design file '../hdl/design/missing.v' in read mode.

Suggestions:
  • File not found - Check path is relative from sim/ directory
  • Use '../hdl/design/file.v' not 'hdl/design/file.v'
  • Verify file exists and spelling is correct
============================================================
```

### Waveform Signal Not Found

```
============================================================
ERROR: Signal not found in waveform
============================================================
  Code: TCL command failed

  Signal '/counter_tb/wrong_name' does not exist

Suggestions:
  • Run list_wave_signals.py to get exact signal names
  • Do not use leading '/' in signal paths (Git Bash issue)
  • Check signal path format: 'module/signal' not '/module/signal'
============================================================
```

## Error Code Reference

**Common ModelSim error codes:**

- **vlog-7**: File not found or cannot open file
- **vlog-2054**: Invalid file specification (possibly a directory)
- **vlog-13069**: Syntax errors with file/line location
- **vsim-4005**: Invalid command argument
- **vsim-3009**: Module not found in work library

## How It Works

The error analysis system:

1. **Parses ModelSim output** using regex patterns to extract error codes, file paths, and line numbers
2. **Provides context-aware suggestions** based on:
   - Specific error codes (e.g., vlog-7 → check file paths)
   - Error message keywords (e.g., "syntax error" → check semicolons)
   - Operation context (compilation, simulation, waveform operations)
3. **Formats output** in a consistent, readable structure

All error analysis is done by `modelsim_controller.analyze_error()` - a common utility used by all CLI scripts.