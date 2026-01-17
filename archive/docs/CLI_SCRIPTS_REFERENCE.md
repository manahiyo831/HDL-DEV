# CLI Scripts Reference

Complete reference for all ModelSim CLI wrapper scripts.

## Table of Contents

- [Overview](#overview)
- [Core Scripts](#core-scripts)
- [Waveform Scripts](#waveform-scripts)
- [Utility Scripts](#utility-scripts)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)

---

## Overview

These CLI scripts provide simple command-line access to ModelSim operations without needing to write Python code.

**Key Features:**
- Simple CLI interface - no Python coding required
- Uses existing proven APIs from `modelsim_controller.py`
- Clear emoji output (✓/✗/⏳) for easy status recognition
- Proper exit codes for shell scripting (0=success, 1=failure)
- Helpful error messages with actionable guidance

**Prerequisites:**
- ModelSim installation (tested with Intel FPGA Edition 20.1+)
- Python 3.7+
- ModelSim must be running with socket server for most scripts

---

## IMPORTANT: Signal Path Specification

**Signal paths MUST NOT start with slash (`/`).**

- ✓ **Correct:** `"counter_tb/dut/count"`
- ✗ **Wrong:** `"/counter_tb/dut/count"`

**Reason:** Leading slashes cause Git Bash automatic path conversion. Git Bash converts paths like `/counter_tb/...` to `C:/Program Files/Git/counter_tb/...`, which fails in ModelSim.

**Affected Scripts:**
- `add_wave.py` - When specifying signal paths
- `change_wave_format.py` - When specifying signal paths

**Unaffected:** File paths for `compile.py` and `modelsim_start.py` are fine since they don't start with `/`.

---

## Core Scripts

### modelsim_start.py

Start ModelSim GUI with socket server.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py <design_file> <testbench_file> <top_module> [sim_time]
```

**Arguments:**
- `design_file` - Path to design file (e.g., "hdl/design/counter.v")
- `testbench_file` - Path to testbench file (e.g., "hdl/testbench/counter_tb.v")
- `top_module` - Top-level testbench module name
- `sim_time` (optional) - Initial simulation time (default: "1us")

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py "hdl/design/decoder.v" "hdl/testbench/decoder_tb.v" "decoder_tb" "500ns"
```

**What it does:**
1. Launches ModelSim GUI
2. Starts socket server on port 12345
3. Compiles design and testbench
4. Loads simulation
5. Adds all signals to waveform
6. Runs initial simulation
7. Returns control (ModelSim stays running)

**Exit codes:** 0 (success), 1 (failure)

---

### connection_check.py

Verify connection to ModelSim socket server.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/connection_check.py
```

**Arguments:** None

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/connection_check.py
```

**What it does:**
1. Attempts to connect to localhost:12345
2. Sends a test TCL command (`pwd`)
3. Reports connection status and working directory

**Exit codes:** 0 (connected), 1 (not connected)

---

### compile.py

Compile/recompile design files.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/compile.py <design_file> <testbench_file> <top_module>
```

**Arguments (all required):**
- `design_file` - Design file path
- `testbench_file` - Testbench file path
- `top_module` - Top-level module name

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/decoder.v" "hdl/testbench/decoder_tb.v" "decoder_tb"
```

**What it does:**
1. Quits current simulation
2. Compiles design file
3. Compiles testbench file
4. Loads simulation
5. Adds waveforms

**Note:** Does NOT run the simulation. Use `run_sim.py` separately.

**Exit codes:** 0 (success), 1 (compilation error)

---

### run_sim.py

Run simulation for specified time.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py <time>
```

**Arguments:**
- `time` - Simulation time with units (e.g., "1us", "500ns", "10ms")

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "500ns"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "10ms"
```

**What it does:**
1. Runs simulation for specified time
2. Automatically refreshes waveform
3. Zooms waveform to full view

**Exit codes:** 0 (success), 1 (failure)

---

## Waveform Scripts

### add_wave.py

Add signal(s) to waveform display.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py                    # Add all signals recursively
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py <signal_path>      # Add specific signal
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py <sig1> <sig2> ...  # Add multiple signals
```

**Arguments:**
- No args: Add all signals recursively
- Signal paths: Add specified signals

**Examples:**
```bash
# Add all signals
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py

# Add specific signal
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py "counter_tb/dut/count"

# Add multiple signals
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py "counter_tb/clk" "counter_tb/reset" "counter_tb/dut/count"
```

**What it does:**
1. Adds specified signals (or all signals if no args)
2. Refreshes waveform display

**Exit codes:** 0 (success), 1 (failure)

---

### change_wave_format.py

Change signal display format in waveform.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py <signal_path> <format>
```

**Arguments:**
- `signal_path` - Full hierarchical signal path
- `format` - Display format: `binary`, `hex`, `unsigned`, `signed`, `octal`, `ascii`

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/dut/count" "unsigned"
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/dut/data" "hex"
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/dut/state" "binary"
```

**What it does:**
1. Changes display format of specified signal
2. Refreshes waveform display

**Exit codes:** 0 (success), 1 (failure)

---

### zoom_waveform.py

Adjust waveform zoom level.

**Usage:**
```bash
# Full view mode
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py full

# Range view mode
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py <start_time> <end_time>
```

**Arguments:**
- Mode 1: `full` - Zoom to show entire simulation
- Mode 2: `start_time` and `end_time` - Zoom to specific range

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py full
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py "100ns" "500ns"
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py "1us" "2us"
```

**Exit codes:** 0 (success), 1 (failure)

---

### refresh_waveform.py

Refresh waveform display.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/refresh_waveform.py
```

**Arguments:** None

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/refresh_waveform.py
```

**What it does:**
1. Refreshes waveform display
2. Zooms to full view

**Exit codes:** 0 (success), 1 (failure)

---

### list_wave_signals.py

List signals currently displayed in wave window.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py              # Simple list
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py --verbose    # Show format info
```

**Arguments:**
- `--verbose` or `-v` (optional) - Show detailed format information

**Examples:**
```bash
# Simple list
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py

# Verbose output with format info
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py --verbose
```

**What it does:**
1. Exports wave window configuration to temporary file
2. Parses file to extract signal list and formats
3. Displays signals currently in wave window
4. Shows radix (display format) for each signal

**Output Example:**
```
============================================================
Signals in Wave Window (5 total)
============================================================
1. /counter_tb/clk
2. /counter_tb/rst_n
3. /counter_tb/count [unsigned]
4. /counter_tb/dut/clk
5. /counter_tb/dut/rst_n
```

**Use case:**
- **Before changing signal format**: List signals to find exact signal name
- **Verify wave contents**: Check which signals are displayed
- **Get signal names for scripting**: Extract signal paths for automation

**Important workflow:**
```bash
# 1. First, list signals to find the exact name
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py

# 2. Then, change format using the correct name
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/count" "unsigned"
```

**Exit codes:** 0 (success), 1 (failure)

---

### capture_screenshot.py

Capture screenshot of ModelSim window or panel.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py              # Entire ModelSim window
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py <target>     # Specific panel
```

**Arguments:**
- `target` (optional) - Panel to capture:
  - No argument: entire ModelSim window (default)
  - `wave`: Waveform panel
  - `transcript`: Transcript panel
  - `objects`: Objects panel
  - `processes`: Processes panel
  - `signals`: Signals panel
  - `structure`: Structure panel

**Examples:**
```bash
# Capture entire window
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py

# Capture wave panel only
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py wave

# Capture transcript
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py transcript
```

**What it does:**
1. Connects to ModelSim socket server
2. Captures screenshot of specified window/panel
3. Saves to `temp/modelsim_{target}.png`
4. Reports resolution and file path

**Output:**
```
============================================================
Screenshot Details
============================================================
Target:     wave
Path:       D:\Claude\HDL-DEV\temp\modelsim_wave.png
Resolution: 1091 x 320
```

**Use cases:**
- **Visual verification**: Capture waveforms for documentation
- **Debug assistance**: Share screenshots when asking for help
- **Report generation**: Include waveforms in test reports
- **AI verification**: Allow Claude to view wave window contents

**Exit codes:** 0 (success), 1 (failure)

---

## Utility Scripts

### restart_sim.py

Restart simulation from time 0.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/restart_sim.py
```

**Arguments:** None

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/restart_sim.py
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"  # Run after restart
```

**What it does:**
- Resets simulation to time 0
- Keeps waveforms intact

**Exit codes:** 0 (success), 1 (failure)

---

### quit_sim.py

Quit current simulation.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/quit_sim.py
```

**Arguments:** None

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/quit_sim.py
```

**What it does:**
- Exits current simulation
- Keeps ModelSim GUI open

**Exit codes:** 0 (success), 1 (failure)

---

### analyze_results.py

Analyze test results from simulation.

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py           # Standard output
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py --verbose # Detailed analysis
```

**Arguments:**
- `--verbose` (optional) - Show detailed analysis

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py --verbose
```

**What it does:**
1. Reads `sim/transcript` file
2. Searches for `TEST_RESULT: PASS/FAIL` markers
3. Extracts compilation errors and warnings
4. Reports summary

**Exit codes:** 0 (tests passed), 1 (tests failed or errors found)

---

### get_transcript.py

Read ModelSim transcript (simulation log).

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py [lines]
```

**Arguments:**
- `lines` (optional) - Number of lines to show (default: 50, "all" for entire file)

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py        # Last 50 lines
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 100    # Last 100 lines
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py all    # Entire transcript
```

**What it does:**
- Reads `sim/transcript` file directly (no ModelSim connection needed)
- Highlights `TEST_RESULT:`, `Error:`, `Warning:` lines

**Exit codes:** Always 0 (read-only operation)

---

### execute_tcl.py

Execute arbitrary TCL command (last resort).

**Usage:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py <tcl_command>
```

**Arguments:**
- `tcl_command` - Any valid TCL command

**Examples:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py "pwd"
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py "radix -hex /counter_tb/dut/count"
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py "wave zoom range 100ns 500ns"
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py "examine /counter_tb/dut/count"
```

**What it does:**
- Executes the provided TCL command directly
- Displays command output

**Use cases:**
- Commands not covered by other scripts
- Testing new TCL commands
- Advanced debugging operations

**Exit codes:** 0 (success), 1 (failure)

---

## Exit Codes

All scripts follow standard exit code conventions:

- **0**: Success - Command completed successfully
- **1**: Failure - Command failed (compilation error, connection error, test failure, etc.)

**Use in shell scripts:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
if [ $? -eq 0 ]; then
    echo "Compilation successful"
    python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
else
    echo "Compilation failed"
    exit 1
fi
```

---

## Troubleshooting

### "Cannot connect to ModelSim"

**Cause:** ModelSim socket server is not running.

**Solution:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"
```

---

### "Compilation failed"

**Causes:**
- Syntax errors in Verilog/VHDL code
- Incorrect file paths
- Missing dependencies

**Solutions:**
1. Check the error messages in output
2. Verify file paths are correct (use forward slashes)
3. Ensure paths are relative from project root
4. Read full errors: `python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py`

---

### "No TEST_RESULT found"

**Cause:** Testbench doesn't include `TEST_RESULT:` markers.

**Solution:** Add to your testbench:
```verilog
if (test_passed) begin
    $display("TEST_RESULT: PASS - All tests passed");
end else begin
    $display("TEST_RESULT: FAIL - Test failed: reason");
end
```

---

### Signal not found

**Cause:** Incorrect signal path or signal doesn't exist.

**Solution:**
1. Check signal hierarchy in ModelSim GUI
2. Ensure path starts with `/` and includes full hierarchy
3. Example: `/counter_tb/dut/count` not just `count`

---

### Waveform not updating

**Cause:** Waveform needs manual refresh.

**Solution:**
```bash
python .claude/skills/modelsim-hdl-dev/scripts/refresh_waveform.py
```

Or included automatically in `run_sim.py`.

---

## Complete Workflow Example

```bash
# ===================================================================
# Complete HDL Development Workflow
# ===================================================================

# Step 1: Start ModelSim (once per session)
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py \
    "hdl/design/counter.v" \
    "hdl/testbench/counter_tb.v" \
    "counter_tb" \
    "1us"

# Step 2: Fast Iteration Loop (edit → compile → run → analyze)

# Edit counter.v...
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py

# Edit counter.v again...
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py

# Step 3: Waveform Analysis

# 3.1: List current signals in wave window
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py

# 3.2: Add additional signals if needed
python .claude/skills/modelsim-hdl-dev/scripts/add_wave.py "counter_tb/dut/count"

# 3.3: List again to verify and get exact signal names
python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py

# 3.4: Change signal format (use exact name from list)
python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "counter_tb/count" "unsigned"

# 3.5: Zoom and capture screenshot
python .claude/skills/modelsim-hdl-dev/scripts/zoom_waveform.py "full"
python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py wave

# Step 4: Advanced Operations
python .claude/skills/modelsim-hdl-dev/scripts/execute_tcl.py "examine /counter_tb/dut/count"
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 100

# ===================================================================
# Result: Simple CLI commands, no Python code needed!
# ===================================================================
```

---

## Related Documentation

- [SKILL.md](../D:/Claude/SKILLS/modelsim-hdl-dev/SKILL.md) - Complete skill documentation
- [README.md](../README.md) - Project overview and Python API
- [LESSONS_LEARNED.md](../LESSONS_LEARNED.md) - Technical notes and bug fixes
