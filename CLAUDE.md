# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Required Skills

**IMPORTANT: Before starting any HDL development work, activate these skills:**

1. **modelsim-hdl-dev** - HDL development automation with ModelSim
   - Provides complete autonomous HDL workflow
   - Socket-based fast iteration (60-100x speedup)
   - Automatic test result verification
   - Use for: Creating/modifying Verilog files, running simulations, debugging with waveforms

2. **skill-creator** - Skill development guidance
   - Use when creating or updating skills
   - Provides best practices and templates
   - Use for: Extending this project's capabilities with new skills

**To activate skills:**
```
/modelsim-hdl-dev
/skill-creator
```

The `modelsim-hdl-dev` skill contains detailed workflow instructions, API documentation, examples, and templates that complement this CLAUDE.md file. Always refer to the skill for complete HDL development procedures.

## Workflow Strategy: Parallel Task Execution

**IMPORTANT: Always consider using parallel subagents to optimize workflow and conserve context.**

When working on tasks, proactively evaluate if parallel execution is possible:

1. **Independent Operations** - Tasks that don't depend on each other:
   - Example: Creating multiple HDL modules simultaneously
   - Example: Running simulations for different modules at the same time
   - Example: Analyzing different waveform files in parallel

2. **Research + Implementation** - Combining exploration with development:
   - Example: One agent explores existing code patterns while another writes new module
   - Example: One agent runs simulation while another prepares next test case

3. **Multi-Module Development** - Working on related but separate components:
   - Example: Design module + testbench creation in parallel
   - Example: Creating specification document while another agent implements design

**When to Propose Parallel Execution:**
- If a task involves 2+ independent subtasks, ALWAYS propose using parallel subagents
- Present the parallel approach to the user before starting work
- Explain how parallelization saves context and speeds up completion

**How to Use Parallel Subagents:**
```
Task tool with multiple invocations in a single response
Agent types: general-purpose, Explore, Bash, etc.
```

**Example Proposal:**
"This task involves creating a new PWM module and its testbench. I can work on these in parallel:
- Subagent 1: Create PWM design module
- Subagent 2: Create testbench with test cases
Would you like me to proceed with parallel execution?"

This approach prevents context overflow and completes work faster.

## Project Overview

This is a **Claude + ModelSim Auto-Simulation Environment** for HDL development. The system enables AI-assisted hardware design with real-time simulation feedback. Claude generates Verilog code, Python scripts automatically compile and run it in ModelSim, and results are analyzed in a continuous feedback loop.

**Key Innovation:** ModelSim stays running with a TCP socket server, allowing ultra-fast iteration without restart overhead.

## Environment Setup

- **ModelSim:** Intel FPGA Edition 20.1
  - Path: `C:/intelFPGA/20.1/modelsim_ase/win32aloem`
  - Working directory: `sim/` (all simulations run from here)
- **Python:** 3.7+
- **Dependencies:** Flask 3.0.0, pytest 8.3.4 (see [requirements.txt](requirements.txt))

## Commands

### Python Simulation Modes

**1. Socket API Mode (Fastest - Recommended for Claude)**

**Note:** Scripts are in SKILL location, so Python path adjustment is needed:

```python
from pathlib import Path
import sys

# Add SKILL scripts to Python path
sys.path.insert(0, str(Path(".claude/skills/modelsim-hdl-dev/scripts")))

from modelsim_controller import ModelSimController

# Initialize controller (use Path.cwd() for current directory)
controller = ModelSimController(Path.cwd())

# First time: Start ModelSim GUI with socket server
controller.start_gui_with_server(
    design_files=[Path("hdl/design/counter.v")],
    testbench_file=Path("hdl/testbench/counter_tb.v"),
    top_module="counter_tb",
    sim_time="1us"
)

# After HDL modifications: recompile and run without restart
result = controller.quick_recompile_and_run(sim_time="1us")

# Analyze results automatically
analysis = controller.analyze_simulation(verbose=True, recent_only=True)
if analysis['success']:
    print(analysis['test_results']['message'])
else:
    for error in analysis['errors']['errors']:
        print(error)

controller.disconnect()
```

**2. Using SKILL (Recommended)**

Activate the modelsim-hdl-dev SKILL and use CLI scripts:
```bash
# Start ModelSim
python .claude/skills/modelsim-hdl-dev/scripts/modelsim_start.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"

# Fast iteration
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/analyze_results.py
```

See SKILL documentation for complete usage: `.claude/skills/modelsim-hdl-dev/SKILL.md`

### Testing

View waveforms:
```bash
python .claude/skills/modelsim-hdl-dev/scripts/view_waveform.py                    # Latest waveform
python .claude/skills/modelsim-hdl-dev/scripts/view_waveform.py --list             # List all waveforms
python .claude/skills/modelsim-hdl-dev/scripts/view_waveform.py results/waveforms/sim_20260114_195517.wlf
```

### ModelSim TCL Commands (in Transcript or via Python)

```tcl
quit -sim                              # Exit current simulation
vlog -work work ../hdl/design/file.v   # Compile design (relative path from sim/)
vsim work.module_tb                    # Load simulation
onfinish stop                          # Prevent $finish dialog
add wave -r /*                         # Add all signals to waveform
run 1us                                # Execute simulation
restart -f                             # Restart from time 0
wave zoom full                         # Zoom waveform to fit window
```

## Architecture

### Directory Structure

```
HDL-DEV/
├── .claude/skills/
│   └── modelsim-hdl-dev/   - SKILL with all automation scripts (CLI + internal)
├── hdl/
│   ├── design/          - Verilog design files (.v)
│   └── testbench/       - Testbench files (*_tb.v)
├── sim/
│   ├── work/            - Compiled library (auto-generated)
│   └── transcript       - ModelSim execution log (analyze for errors/results)
└── docs/
    └── HOW_TO_RUN_NEW_SIMULATION.md - Workflow examples
```

### Result Analysis System

The controller reads `sim/transcript` to autonomously detect:
- **Compilation errors**: `** Error: (vlog-*)`
- **Warnings**: `** Warning:`
- **Test results**: `TEST_RESULT: PASS` or `TEST_RESULT: FAIL` markers

**Testbench Convention:**
```verilog
$display("TEST_RESULT: PASS - Counter is functioning (final count: %d)", count);
$display("TEST_RESULT: FAIL - Counter did not increment");
```

## Development Workflow (Claude AI Loop)

1. **Generate/Modify HDL**
   - Create design: `hdl/design/<module>.v`
   - Create testbench: `hdl/testbench/<module>_tb.v`
   - Use `$display("TEST_RESULT: ...")` for pass/fail detection

2. **Run Simulation**
   ```python
   controller.quick_recompile_and_run(sim_time="1us")
   ```

3. **Analyze Results**
   ```python
   analysis = controller.analyze_simulation(verbose=True, recent_only=True)
   ```

4. **Check Success**
   - If `analysis['success']` is True and test results show PASS → Done
   - If errors found → Fix HDL and repeat from step 2
   - No ModelSim restart needed between iterations

5. **View Waveforms** (optional)
   - Waveforms auto-update in GUI after `refresh_waveform()`
   - See SKILL documentation for waveform viewing, signal listing, and screenshot capture

## Path Handling (Critical for Windows)

**Always use forward slashes (`/`) in Python when passing paths to ModelSim:**
```python
# Correct
design_files = [Path("hdl/design/counter.v")]
path_str = str(design_files[0]).replace("\\", "/")

# Wrong - backslashes get mangled in Bash tool
path_str = "hdl\\design\\counter.v"
```

**Relative paths from `sim/` directory:**
- Design files: `../hdl/design/file.v`
- Testbench files: `../hdl/testbench/file_tb.v`

## Important TCL Conventions (from LESSONS_LEARNED.md)

1. **Error handling:** Use `catch {command}` not `if {$? != 0}`
2. **$finish behavior:** Set `onfinish stop` to prevent dialog
3. **JSON boolean issues:** Check empty lists before boolean type checking
4. **Transcript analysis:** Last 100 lines only (`recent_only=True`) to ignore old errors

## Simulation Time Guidelines

- **Counters/Simple logic:** 1us - 10us
- **Pulse generators:** 3-10ms (depends on pulse period)
- **Complex protocols:** 100us - 1ms
- Use `$finish` in testbench to auto-terminate when test completes

## Example Modules

**counter.v**: 8-bit synchronous counter with enable and async reset
- Testbench: Verifies reset, enable, increment
- Runtime: ~1us
- Location: [hdl/design/counter.v](hdl/design/counter.v)

**pulse_generator.v**: 1ms pulse generator (1MHz clock)
- Testbench: Checks pulse interval (1ms ±1%), requires 3 pulses
- Runtime: 3.5ms
- Location: [hdl/design/pulse_generator.v](hdl/design/pulse_generator.v)

## Troubleshooting

**Socket connection fails:**
```python
# Increase connection delay if ModelSim GUI slow to start
controller.start_gui_with_server(..., connect_delay=5.0)
```

**Old errors showing in analysis:**
```python
# Use recent_only=True to check only last 100 lines
analysis = controller.analyze_simulation(recent_only=True)
```

**Compilation errors:**
- Check `sim/transcript` for full error messages
- Verify file paths (relative from `sim/`, forward slashes)
- Ensure `work` library exists: `vlib work`

**Waveform not updating:**
```python
controller.refresh_waveform()  # Explicitly refresh after run
```

**ModelSim GUI unresponsive:**
- Close and restart ModelSim
- Socket server automatically starts on next `start_gui_with_server()`

## Complete Self-Contained Example

```python
from pathlib import Path
import sys

# Add SKILL scripts to Python path
sys.path.insert(0, str(Path(".claude/skills/modelsim-hdl-dev/scripts")))

from modelsim_controller import ModelSimController

# Setup (use Path.cwd() for current directory)
controller = ModelSimController(Path.cwd())

# First run: Start GUI
controller.start_gui_with_server(
    design_files=[Path("hdl/design/counter.v")],
    testbench_file=Path("hdl/testbench/counter_tb.v"),
    top_module="counter_tb",
    sim_time="1us"
)

# Modify counter.v...

# Fast re-simulation
result = controller.quick_recompile_and_run(sim_time="1us")
if result['success']:
    analysis = controller.analyze_simulation(verbose=True, recent_only=True)
    if analysis['success'] and analysis['test_results']['found']:
        if 'PASS' in analysis['test_results']['message']:
            print("✓ Test passed!")
        else:
            print("✗ Test failed:", analysis['test_results']['message'])
    elif analysis['errors']['errors']:
        print("✗ Compilation/simulation errors:")
        for error in analysis['errors']['errors'][:5]:
            print(f"  {error}")
else:
    print("✗ Recompile failed:", result['message'])

controller.disconnect()
```

## Additional Documentation

- [README.md](README.md) - Full API reference, detailed usage examples
- [docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md) - Technical implementation notes, TCL gotchas
- [HDL_DESIGN_SPECIFICATION_TEMPLATE.md](HDL_DESIGN_SPECIFICATION_TEMPLATE.md) - Template for documenting new designs
- [docs/HOW_TO_RUN_NEW_SIMULATION.md](docs/HOW_TO_RUN_NEW_SIMULATION.md) - Step-by-step guide for switching modules

## Japanese Documentation

Most documentation is in Japanese (プロジェクトドキュメントは日本語). Key files:
- README.md: 概要と使い方
- docs/LESSONS_LEARNED.md: 技術的学習記録
- docs/HOW_TO_RUN_NEW_SIMULATION.md: 新規シミュレーション手順
