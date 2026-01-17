---
name: modelsim-hdl-dev
description: Automated HDL development environment with ModelSim socket-based control. Enables Claude to autonomously generate, simulate, and verify HDL designs with complete result analysis. Use this skill when (1) Creating or modifying Verilog/VHDL design files, (2) Running ModelSim simulations with automatic result verification, (3) Implementing testbenches with TEST_RESULT markers, (4) Debugging HDL with waveform analysis, (5) Setting up fast-iteration HDL development workflows. Supports socket communication for rapid recompile-simulate cycles without restarting ModelSim.
---

# ModelSim HDL Automated Development Environment

## Overview

Complete autonomous HDL development loop for Verilog/VHDL designs:

```
Claude → HDL Generation → ModelSim Simulation → Result Analysis → Fixes → Repeat
```

**Key Features:**
- **Autonomous verification** - Claude automatically verifies simulation results
- **Ultra-fast iteration** - Socket communication eliminates ModelSim restarts (~95% time saving)
- **Automatic pass/fail detection** - TEST_RESULT: markers enable autonomous testing
- **Real-time waveform viewing** - Visual verification while Claude develops

**Time Savings:**
- Traditional: ~5-10 minutes per iteration
- With this skill: ~5-30 seconds per iteration
- **Overall speedup: ~10x faster**

---

## Quick Start

**Important:** Run all commands from your project root directory (where hdl/, sim/ folders are located).

**Step 1: Start ModelSim (one-time)**:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim_server.py
```

**Step 2: Verify connection**:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/connection_check.py
```

**Step 3: Load design**:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/load_module.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"
```

**Step 4: Fast iteration after editing HDL**:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50
```

**For complete CLI workflow, see "CLI Scripts" section below**

---

## CLI Scripts (Recommended for Claude)

All scripts are located in `.claude/skills/modelsim-hdl-dev/scripts/`. For brevity, examples below use `$SKILL/` to represent `.claude/skills/modelsim-hdl-dev/`.

### Quick Start

```bash
# 1. Start ModelSim (one-time)
python $SKILL/scripts/start_modelsim_server.py

# 2. Verify connection
python $SKILL/scripts/connection_check.py

# 3. Load design
python $SKILL/scripts/load_module.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"

# 4. Fast iteration after HDL changes
python $SKILL/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python $SKILL/scripts/run_sim.py "1us"
python $SKILL/scripts/get_transcript.py 50

# 5. Waveform analysis
python $SKILL/scripts/list_wave_signals.py  # Get signal names first
python $SKILL/scripts/change_wave_format.py "counter_tb/count" "unsigned"
python $SKILL/scripts/capture_screenshot.py "wave"
```

### Available Scripts

**Simulation Control:**

| Script | Purpose |
|--------|---------|
| `start_modelsim_server.py` | Start ModelSim GUI with socket server (one-time) |
| `load_module.py` | Load design and run initial simulation |
| `compile.py` | Recompile design after changes |
| `run_sim.py` | Run simulation for specified time |
| `restart_sim.py` | Restart simulation to time 0 |
| `quit_sim.py` | Quit current simulation (GUI stays open) |
| `connection_check.py` | Verify socket connection to ModelSim |

**Results & Analysis:**

| Script | Purpose |
|--------|---------|
| `get_transcript.py` | Read simulation transcript (last N lines) |
| `execute_tcl.py` | Execute arbitrary TCL command |

**Waveform Control:**

| Script | Purpose |
|--------|---------|
| `add_wave.py` | Add signals to waveform |
| `list_wave_signals.py` | List current signals in waveform |
| `change_wave_format.py` | Change signal display format (hex/dec/bin) |
| `zoom_waveform.py` | Zoom waveform (full or time range) |
| `refresh_waveform.py` | Refresh waveform display |
| `capture_screenshot.py` | Capture ModelSim panel screenshot |
| `view_waveform.py` | Open saved waveform file (.wlf) |

**CRITICAL:** Signal paths must NOT start with `/` (Git Bash path conversion issues). Use `"counter_tb/count"`, not `"/counter_tb/count"`.

**Best practice:** Always run `list_wave_signals.py` first to get exact signal names before using `change_wave_format.py`.

---

## Design Workflow

### For Complex Designs

When creating non-trivial HDL modules (with multiple sub-modules, state machines, registers, or complex protocols), **start with a design specification** before writing code.

**Recommended Process:**

1. **Create Design Specification** - Use the comprehensive template:
   - [assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md](assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md)
   - **Fill in only relevant sections** - The template is comprehensive; omit sections that don't apply to your design
   - Key sections: Interface signals, timing requirements, state machines, register maps
   - Optional sections can be skipped based on design complexity

2. **Implement HDL** - Write Verilog/VHDL based on the specification
   - Reference the specification while coding
   - Maintain traceability between spec and implementation

3. **Simulate and Iterate** - Use this skill's fast iteration workflow
   - Quick recompile and run (~5-30 seconds per iteration)
   - Autonomous verification with TEST_RESULT: markers

**Benefits:**
- **Clarity** - Forces you to think through the design before coding
- **Communication** - Provides clear documentation for review
- **Verification** - Testbenches can directly verify against specification
- **Maintenance** - Future changes are easier with documented design intent

**When to use the template:**
- Multi-module designs
- Designs with state machines or complex control logic
- Modules with configuration registers
- Interfaces using standard protocols (AXI, APB, etc.)
- Any design where specification clarity is valuable

**For simple modules** (counters, shift registers, basic combinational logic), you can skip the specification and go straight to implementation with testbench.

---

## Advanced Waveform Control

### Waveform Zoom

Focus on specific time ranges or events for detailed inspection.

```bash
# Zoom to specific time range
python $SKILL/scripts/zoom_waveform.py range 380ns 450ns

# Return to full view
python $SKILL/scripts/zoom_waveform.py full
```

**Use cases:**
- Inspect reset sequences
- Focus on pulse occurrences
- Examine specific clock cycles
- Debug timing violations

### Signal Display Format

Change signal display formats between binary, decimal, hexadecimal, and octal.

**Recommended Workflow (Two-Step Process):**

**Step 1: List signals to get exact names**
```bash
python $SKILL/scripts/list_wave_signals.py
```

This will output signal names like:
```
1. /counter_tb/clk
2. /counter_tb/rst_n
3. /counter_tb/count
4. /counter_tb/dut/clk
5. /counter_tb/dut/rst_n
6. /counter_tb/dut/count
```

**Step 2: Change format using exact signal name (without leading `/`)**
```bash
# Change to decimal (unsigned)
python $SKILL/scripts/change_wave_format.py "counter_tb/dut/count" "unsigned"

# Change to hexadecimal
python $SKILL/scripts/change_wave_format.py "counter_tb/state" "hex"

# Change to binary
python $SKILL/scripts/change_wave_format.py "counter_tb/data" "binary"
```

**Available formats:** binary, hex, unsigned, signed, octal, ascii

**Use cases:**
- View counters in decimal for readability
- Debug address buses in hexadecimal
- Verify byte values in decimal or hex

**Important Notes:**
- Always list signals first to get exact signal names
- DO NOT use leading `/` in arguments (Git Bash path conversion issue)
- The script internally adds `/` prefix for the TCL command
- ModelSim uses `property wave -radix` command to change formats

---

## Screenshot Capture

Capture screenshots of ModelSim panels for visual verification and documentation.

### Supported Targets

- **modelsim** - Full ModelSim window (includes all panels)
- **wave** - Waveform display panel only
- **objects** - Objects/signals list panel
- **processes** - Processes list panel
- **transcript** - Console output panel
- **sim** - Structure/Instance hierarchy panel

### Usage

```bash
# Capture waveform panel
python $SKILL/scripts/capture_screenshot.py "wave"
# Saves to: screenshots/screenshot.png

# Capture full window
python $SKILL/scripts/capture_screenshot.py "modelsim"
# Saves to: screenshots/screenshot.png (overwrites)

# Capture transcript
python $SKILL/scripts/capture_screenshot.py "transcript"
# Saves to: screenshots/screenshot.png (overwrites)

# Custom output path
python $SKILL/scripts/capture_screenshot.py "wave" "results/my_wave.png"
```

**Arguments:**
- First argument: Target panel (modelsim, wave, objects, processes, transcript, sim)
- Second argument (optional): Custom output path

**Output:**
- Default location: `screenshots/` (in current directory)
- Filename: `screenshot.png` (fixed, always overwrites)
- Custom path: Specify as second argument

### Implementation Details

**Key technique:**
- Uses Tcl `winfo id` command to get window handles from widget paths
- Direct HWND capture using Win32 BitBlt
- Works with any window size (panels are resizable)
- No coordinate conversion required

---

## Helper Scripts

Two helper scripts for managing ModelSim:

- **load_module.py** - Load/switch designs (auto-starts ModelSim if needed)
- **start_modelsim_server.py** - Manual ModelSim startup (if you prefer separate initialization)

---

## Standard Testbench Format

**Critical:** Add `TEST_RESULT:` markers for autonomous verification

```verilog
module my_module_tb;
    // Your test logic...

    initial begin
        $display("=== Test Start ===");

        // Run tests
        #1000;

        // REQUIRED: Add TEST_RESULT marker
        if (all_tests_passed) begin
            $display("TEST_RESULT: PASS - All tests passed");
        end else begin
            $display("TEST_RESULT: FAIL - Test failed: reason");
        end

        $finish;
    end

    // RECOMMENDED: Add watchdog timer
    initial begin
        #100000;  // Timeout
        $display("TEST_RESULT: FAIL - Timeout");
        $finish;
    end
endmodule
```

**Format Rules:**
- Must contain `TEST_RESULT:`
- Followed by `PASS` or `FAIL`
- Include descriptive message
- Claude automatically detects and parses these

**See:** [assets/examples/counter_tb.v](assets/examples/counter_tb.v) for complete example

---

## Recommended Project Structure

```
your_project/
├── .claude/skills/
│   └── modelsim-hdl-dev/  # This SKILL (CLI scripts included)
├── hdl/
│   ├── design/           # Design files (.v, .vhd)
│   │   ├── counter.v
│   │   └── decoder.v
│   └── testbench/        # Testbench files
│       ├── counter_tb.v
│       └── decoder_tb.v
└── sim/                  # ModelSim working directory (IMPORTANT: Read below)
    ├── work/             # Compiled library (auto-generated)
    ├── transcript        # Simulation log (read this for results)
    └── wave_signals.do   # Wave configuration export (temporary)
```

**IMPORTANT: About the `sim/` Directory**

ModelSim executes all TCL commands from within the `sim/` directory. This means:
- All file paths in TCL commands are relative to `sim/`
- Design files are referenced as `../hdl/design/counter.v` (from sim's perspective)
- The `work/` library and `transcript` log are created in `sim/`
- This is why paths use `../` prefix when passed to ModelSim

**Why this matters:**
- When debugging, remember that ModelSim's "current directory" is `sim/`
- The `transcript` file in `sim/` contains all simulation output
- Waveform files (.wlf) are also saved in `sim/`

**Usage Notes:**
- Run all CLI scripts from project root (where hdl/, sim/ are located)
- All file paths in scripts are relative from project root
- Use forward slashes (`/`) even on Windows
- Design files: `hdl/design/module.v`
- Testbench files: `hdl/testbench/module_tb.v`

---

## Configuration

### ModelSim Installation Path

If your ModelSim is installed at a different location, update `MODELSIM_DEFAULT_PATH` in these scripts:

- `scripts/modelsim_start.py`
- `scripts/view_waveform.py`

```python
# ==========================================
# ModelSim Configuration
# ==========================================
MODELSIM_DEFAULT_PATH = "C:/intelFPGA/21.1/modelsim_ase/win32aloem"
# ⬆️ Change this line to your installation path
# ==========================================
```

**Common paths:**
- Intel FPGA: `C:/intelFPGA/{version}/modelsim_ase/win32aloem`
- Questa Sim: `C:/questasim/win64`

---

## Error Handling

All CLI scripts provide detailed, user-friendly error messages with automatic analysis of ModelSim errors. When an error occurs, you'll see:

**Error Message Structure:**
- **What went wrong** - Clear error summary (e.g., "Compilation error in hdl/design/counter.v")
- **Where it happened** - File path and line number (extracted from ModelSim output)
- **Why it happened** - Error code (e.g., vlog-13069, vsim-4005) and detailed message
- **How to fix** - Context-specific suggestions based on error type

### Example Error Outputs

**Compilation Error:**
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

**File Not Found Error:**
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

**Waveform Signal Not Found:**
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

### Error Code Reference

**Common ModelSim error codes:**
- **vlog-7**: File not found or cannot open file
- **vlog-2054**: Invalid file specification (possibly a directory)
- **vlog-13069**: Syntax errors with file/line location
- **vsim-4005**: Invalid command argument
- **vsim-3009**: Module not found in work library

### How It Works

The error analysis system:
1. **Parses ModelSim output** using regex patterns to extract error codes, file paths, and line numbers
2. **Provides context-aware suggestions** based on:
   - Specific error codes (e.g., vlog-7 → check file paths)
   - Error message keywords (e.g., "syntax error" → check semicolons)
   - Operation context (compilation, simulation, waveform operations)
3. **Formats output** in a consistent, readable structure

All error analysis is done by `modelsim_controller.analyze_error()` - a common utility used by all CLI scripts.

---

## Troubleshooting

**Primary debugging tool:** Always check ModelSim transcript first when troubleshooting:

```bash
python $SKILL/scripts/get_transcript.py 50  # Last 50 lines
```

**For all troubleshooting scenarios, common errors, debugging techniques, and solutions:** See [references/troubleshooting.md](references/troubleshooting.md)

---

## Examples

### Example 1: Counter

Basic 8-bit counter with enable and reset.

- Design: [assets/examples/counter.v](assets/examples/counter.v)
- Testbench: [assets/examples/counter_tb.v](assets/examples/counter_tb.v)

**Features demonstrated:**
- Clock generation
- Reset sequence
- Enable control
- TEST_RESULT: markers
- Watchdog timer

---

### Example 2: Pulse Generator (1ms)

Generates 1 pulse every 1ms with 1MHz clock input.

- Design: [assets/examples/pulse_gen_1ms.v](assets/examples/pulse_gen_1ms.v)
- Testbench: [assets/examples/pulse_gen_1ms_tb.v](assets/examples/pulse_gen_1ms_tb.v)

**Features demonstrated:**
- Parameter-based timing (COUNT_MAX = 1000-1)
- Pulse interval verification with tolerance (±1%)
- Multiple pulse detection (3 pulses)
- Real-world timing constraints (1MHz clock, 1ms period)

---

### Templates

**Design Specification Template:**
[assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md](assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md)

Comprehensive HDL design specification template for complex designs:
- Interface and signal definitions
- Timing and protocol specifications
- State machine documentation
- Register maps
- Verification scenarios
- **Note:** Fill in only relevant sections; omit sections that don't apply

**Testbench Template:**
[assets/templates/basic_testbench_template.v](assets/templates/basic_testbench_template.v)

Complete testbench skeleton with:
- Clock generation
- Test case structure
- TEST_RESULT: markers
- Watchdog timer
- Best practices

## Best Practices

1. **Use TEST_RESULT: markers** - Enable autonomous verification (`TEST_RESULT: PASS/FAIL`)
2. **Add watchdog timers** - Prevent infinite loops in testbenches
3. **Use load_module.py** - Simplest way to load/switch designs (auto-starts ModelSim if needed)
4. **List signals before changing format** - Run `list_wave_signals.py` first, then `change_wave_format.py`
5. **Check transcript for errors** - Use `python $SKILL/scripts/get_transcript.py` to read recent output
6. **Keep ModelSim open** - Use socket communication for fast iteration (don't restart between edits)

---

## Files Included

### CLI Scripts (Primary Interface)
- `start_modelsim_server.py` - Start ModelSim GUI with socket server
- `load_module.py` - Load design and run initial simulation
- `compile.py` - Recompile design after changes
- `run_sim.py` - Run simulation for specified time
- `restart_sim.py` - Restart simulation to time 0
- `quit_sim.py` - Quit current simulation
- `connection_check.py` - Verify socket connection
- `get_transcript.py` - Read ModelSim transcript
- `execute_tcl.py` - Execute arbitrary TCL commands
- `add_wave.py` - Add signals to waveform
- `list_wave_signals.py` - List signals in waveform
- `change_wave_format.py` - Change signal display format
- `zoom_waveform.py` - Zoom waveform to time range or full
- `refresh_waveform.py` - Refresh waveform display
- `capture_screenshot.py` - Capture ModelSim panel screenshots
- `view_waveform.py` - Open saved waveform file (.wlf)

### References (Documentation)
- `troubleshooting.md` - Common issues and solutions

### Assets (Examples & Templates)
- `examples/counter.v` - 8-bit counter design
- `examples/counter_tb.v` - Counter testbench
- `examples/pulse_gen_1ms.v` - 1ms pulse generator (NEW)
- `examples/pulse_gen_1ms_tb.v` - Pulse generator testbench (NEW)
- `templates/basic_testbench_template.v` - Testbench skeleton
- `templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md` - Design spec template

---

## Requirements

- **ModelSim:** Intel FPGA Edition 20.1 or later (or Questa Sim)
- **Python:** 3.7 or later
- **OS:** Windows (tested on Windows 11)

**Note:** Linux/Mac support possible with minor path adjustments

---

## See Also

- **Troubleshooting:** [references/troubleshooting.md](references/troubleshooting.md)

---

## License

This skill was developed through Claude-assisted collaborative work.

**Author:** Claude Code
**Date:** 2026-01-14
