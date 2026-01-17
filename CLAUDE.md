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

**1. Using SKILL CLI Scripts (Recommended)**

Activate the modelsim-hdl-dev SKILL and use CLI scripts:
```bash
# Step 1: Start ModelSim (one-time)
python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim_server.py

# Step 2: Load design and run initial simulation
python .claude/skills/modelsim-hdl-dev/scripts/load_module.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"

# Step 3: Check results
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50

# Step 4: Fast iteration after HDL changes
python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"
python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50
```

See SKILL documentation for complete usage: `.claude/skills/modelsim-hdl-dev/SKILL.md`

**2. Python Infrastructure Layer (Advanced)**

For custom automation, use the lean infrastructure layer directly:

```python
from pathlib import Path
import sys

# Add SKILL internal scripts to Python path
sys.path.insert(0, str(Path(".claude/skills/modelsim-hdl-dev/scripts/internal")))

from modelsim_controller import ModelSimController

# Initialize controller
controller = ModelSimController(Path.cwd())

# Connect to running ModelSim server
if controller.connect():
    # Execute TCL commands
    result = controller.execute_tcl("wave zoom full")

    # Read transcript
    transcript = controller.read_transcript(lines=50)
    print(transcript)

    controller.disconnect()
```

**Note:** The infrastructure layer provides basic socket communication and TCL execution. For complete workflows, use the CLI scripts documented above and in SKILL.md.

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
└── archive/docs/     - Archived documentation
    └── HOW_TO_RUN_NEW_SIMULATION.md - Workflow examples (archived)
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

## Development Workflow

For complete HDL development workflow with ModelSim, see `.claude/skills/modelsim-hdl-dev/SKILL.md`.

**Quick CLI Workflow:**

1. **Start ModelSim** (one-time)
   ```bash
   python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim_server.py
   ```

2. **Load design**
   ```bash
   python .claude/skills/modelsim-hdl-dev/scripts/load_module.py "hdl/design/<module>.v" "hdl/testbench/<module>_tb.v" "<module>_tb" "1us"
   ```

3. **Edit HDL files**
   - Create/modify design: `hdl/design/<module>.v`
   - Create/modify testbench: `hdl/testbench/<module>_tb.v`
   - Use `$display("TEST_RESULT: PASS/FAIL - ...")` for automated result detection

4. **Recompile and run**
   ```bash
   python .claude/skills/modelsim-hdl-dev/scripts/compile.py "hdl/design/<module>.v" "hdl/testbench/<module>_tb.v" "<module>_tb"
   python .claude/skills/modelsim-hdl-dev/scripts/run_sim.py "1us"
   ```

5. **Check results**
   ```bash
   python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50
   ```

6. **Repeat steps 3-5** - No ModelSim restart needed

7. **View waveforms** (optional)
   ```bash
   python .claude/skills/modelsim-hdl-dev/scripts/list_wave_signals.py
   python .claude/skills/modelsim-hdl-dev/scripts/change_wave_format.py "signal/path" "unsigned"
   python .claude/skills/modelsim-hdl-dev/scripts/capture_screenshot.py "wave"
   ```

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

## Important TCL Conventions (from archive/docs/LESSONS_LEARNED.md)

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
```bash
# Check if server is running
python .claude/skills/modelsim-hdl-dev/scripts/connection_check.py

# Restart ModelSim if needed (close ModelSim GUI first)
python .claude/skills/modelsim-hdl-dev/scripts/start_modelsim_server.py
```

**Compilation errors:**
```bash
# View recent transcript for error details
python .claude/skills/modelsim-hdl-dev/scripts/get_transcript.py 50
```
- Verify file paths (relative from `sim/`, forward slashes)
- Check syntax errors in Verilog files
- Ensure `work` library exists: `vlib work` in `sim/` directory

**Waveform not updating:**
```bash
# Manually refresh waveform
python .claude/skills/modelsim-hdl-dev/scripts/refresh_waveform.py
```

**ModelSim GUI unresponsive:**
- Close and restart ModelSim GUI
- Socket server automatically starts on next `start_modelsim_server.py`
- Check `sim/transcript` for error messages

**For complete troubleshooting guide, see SKILL.md**

## Additional Documentation

- [README.md](README.md) - Full API reference, detailed usage examples
- [archive/docs/LESSONS_LEARNED.md](archive/docs/LESSONS_LEARNED.md) - Technical implementation notes, TCL gotchas (archived)
- [.claude/skills/modelsim-hdl-dev/assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md](.claude/skills/modelsim-hdl-dev/assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md) - Template for documenting new designs
- [archive/docs/HOW_TO_RUN_NEW_SIMULATION.md](archive/docs/HOW_TO_RUN_NEW_SIMULATION.md) - Step-by-step guide for switching modules (archived)

## Japanese Documentation

Most documentation is in Japanese (プロジェクトドキュメントは日本語). Key files:
- README.md: 概要と使い方
- archive/docs/LESSONS_LEARNED.md: 技術的学習記録（アーカイブ済み）
- archive/docs/HOW_TO_RUN_NEW_SIMULATION.md: 新規シミュレーション手順（アーカイブ済み）
