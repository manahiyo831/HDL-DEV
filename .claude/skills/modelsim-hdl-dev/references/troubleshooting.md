# Troubleshooting Guide

Common issues and solutions for ModelSim HDL automation with CLI scripts.

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Socket Communication](#socket-communication)
- [Compilation Errors](#compilation-errors)
- [Simulation Issues](#simulation-issues)
- [Waveform Display](#waveform-display)
- [TCL Errors](#tcl-errors)

---

## Installation & Setup

### ModelSim Not Found

**Symptom:**
```
ERROR: ModelSim not found at: C:/intelFPGA/20.1/modelsim_ase/win32aloem
```

**Solution:**

1. **Verify installation path:**
   ```bash
   ls "C:/intelFPGA/20.1/modelsim_ase/win32aloem/vsim.exe"
   ```

2. **Update MODELSIM_DEFAULT_PATH:**

   Open these files and modify the constant at the top:
   - `scripts/modelsim_controller.py`
   - `scripts/modelsim_start.py`
   - `scripts/view_waveform.py`

   ```python
   MODELSIM_DEFAULT_PATH = "C:/intelFPGA/21.1/modelsim_ase/win32aloem"
   # ⬆️ Change this to your ModelSim installation path
   ```

3. **Common paths:**
   - Intel FPGA: `C:/intelFPGA/{version}/modelsim_ase/win32aloem`
   - Questa Sim: `C:/questasim/win64`

---

### Path Issues (Windows)

**Symptom:**
```
** Error: (vlog-7) Failed to open design unit file "hdl\\design\\counter.v"
```

**Problem:**
Windows backslashes (`\`) in file paths.

**Solution:**
Always use forward slashes (`/`):

```bash
# ✓ Correct
python scripts/compile.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb"

# ✗ Wrong
python scripts/compile.py "hdl\\design\\counter.v" ...
```

---

## Socket Communication

### Connection Refused

**Symptom:**
```
Connection attempt 1/10 failed: [WinError 10061] Connection refused
```

**Possible Causes:**

1. **Socket server not started yet**
   - Wait 5-10 seconds after launching ModelSim
   - Check ModelSim transcript for "Socket server started on port 12345"

2. **Port already in use**
   ```bash
   netstat -ano | findstr :12345
   ```

3. **ModelSim crashed or closed**
   - Restart: `python scripts/modelsim_start.py ...`

---

### Server Becomes Unresponsive

**Symptom:**
- Commands hang
- No response from connection_check.py
- Error: "can not find channel"

**Solution:**

1. **Close ModelSim** (File → Exit)

2. **Restart ModelSim:**
   ```bash
   python scripts/modelsim_start.py "hdl/design/counter.v" "hdl/testbench/counter_tb.v" "counter_tb" "1us"
   ```

3. **If error persists:**
   - Kill ModelSim process from Task Manager
   - Delete `sim/transcript` file
   - Restart fresh

---

## Compilation Errors

### Design File Not Found

**Symptom:**
```
** Error: (vlog-7) Failed to open design unit file "../hdl/design/counter.v"
```

**Solution:**

1. **Verify file exists:**
   ```bash
   ls hdl/design/counter.v
   ```

2. **Check path relative to `sim/` directory:**
   ```
   project/
   ├── sim/           ← ModelSim runs from here
   └── hdl/
       └── design/
           └── counter.v  ← Path is ../hdl/design/counter.v
   ```

3. **Use forward slashes**, not backslashes

---

### Syntax Errors in HDL

**Symptom:**
```
** Error: (vlog-13069) counter.v(45): near ";": syntax error
```

**Solution:**

1. **Check the error line** (line 45 in example)

2. **Common mistakes:**
   - Missing semicolons
   - Mismatched `begin`/`end`
   - Wrong module name
   - Undefined signals

3. **Test manually in `sim/` directory:**
   ```bash
   cd sim
   vlog -work work ../hdl/design/counter.v
   ```

---

### Signal Path Issues (Git Bash)

**Symptom:**
```
Error: Can't find signal "/counter_tb/count"
```

**Problem:**
Leading slash (`/`) causes Git Bash path conversion.

**Solution:**

Remove leading slash from signal paths:

```bash
# ✓ Correct
python scripts/change_wave_format.py "counter_tb/count" "unsigned"

# ✗ Wrong (Git Bash converts to C:/Program Files/Git/counter_tb/count)
python scripts/change_wave_format.py "/counter_tb/count" "unsigned"
```

**Best practice:**
Always run `python scripts/list_wave_signals.py` first to get exact signal names.

---

## Simulation Issues

### Check Transcript First

**When troubleshooting ANY issue, ALWAYS check the transcript first:**

```bash
python scripts/get_transcript.py 50  # Last 50 lines
```

Or read the file directly:
```bash
tail -50 sim/transcript
```

The transcript contains the ground truth of what ModelSim actually executed.

---

### TEST_RESULT Not Found

**Symptom:**
```bash
python scripts/analyze_results.py
# Output: "No TEST_RESULT marker found"
```

**Cause:**
Testbench doesn't have `TEST_RESULT:` marker.

**Solution:**

Add to your testbench:
```verilog
// At the end of test
if (test_passed) begin
    $display("TEST_RESULT: PASS - Test description");
end else begin
    $display("TEST_RESULT: FAIL - What failed");
end

$finish;
```

**Format:**
- Must start with `TEST_RESULT:`
- Followed by `PASS` or `FAIL`
- Then dash and description

---

### Simulation Time Too Short/Long

**Symptom:**
- Test doesn't complete
- Or simulation takes forever

**Solution:**

1. **Adjust simulation time:**
   ```bash
   python scripts/run_sim.py "10ms"   # Longer
   python scripts/run_sim.py "100ns"  # Shorter
   ```

2. **Use $finish in testbench** to auto-stop:
   ```verilog
   initial begin
       #1000000;  // Wait 1ms
       $finish;   // Auto-stop
   end
   ```

3. **Add watchdog timer:**
   ```verilog
   initial begin
       #10000000;  // 10ms timeout
       $display("TEST_RESULT: FAIL - Timeout");
       $finish;
   end
   ```

---

## Waveform Display

### Waveform Not Updated

**Symptom:**
After running simulation, waveform doesn't show new data.

**Solution:**

```bash
python scripts/refresh_waveform.py
```

Or manually in ModelSim:
```tcl
wave zoom full
```

---

### Signals Not Added to Waveform

**Symptom:**
Waveform window is empty or missing signals.

**Solution:**

```bash
python scripts/add_wave.py  # Adds all signals recursively
```

Or manually:
```tcl
add wave -r /*
```

---

### Signal Display Format (Binary/Decimal)

**Symptom:**
Count signal shows binary instead of decimal.

**Solution:**

1. **List signals first:**
   ```bash
   python scripts/list_wave_signals.py
   ```

2. **Change format** (use exact name from list, without leading `/`):
   ```bash
   python scripts/change_wave_format.py "counter_tb/count" "unsigned"
   ```

3. **Verify with screenshot:**
   ```bash
   python scripts/capture_screenshot.py wave
   ```

**Note:** Never use leading `/` in signal paths when using Git Bash.

---

## TCL Errors

### TCL Error Checking

**Problem:**
Shell-style error checking doesn't work in TCL:
```tcl
# ✗ Wrong (shell syntax)
vlog design.v
if {$? != 0} {
    puts "ERROR"
}
```

**Solution:**

Use `catch`:
```tcl
# ✓ Correct (TCL syntax)
if {[catch {vlog design.v}]} {
    puts "ERROR: Compilation failed"
    quit -f
}
```

`catch` returns:
- `0` if command succeeded
- `1` if command failed

---

### TCL JSON Conversion Error

**Symptom:**
```
Error: list element in quotes followed by ":" instead of space
    while executing "llength $value"
```

**Cause:**
TCL `llength` command fails on values with colons (e.g., `"unsigned:/signal/path"`).

**Solution:**

This is already fixed in `modelsim_socket_server.tcl`. The `dict_to_json` procedure now uses `catch` to handle invalid list formats.

If you encounter this error, update your `modelsim_socket_server.tcl` from the skill.

---

## Quick Reference

### Connection Issues → Check:
- Socket server started? (check transcript)
- Port 12345 available? (`netstat -ano | findstr :12345`)
- Wait 5-10 seconds after ModelSim launch
- Use `python scripts/connection_check.py`

### Compilation Issues → Check:
- File paths use forward slashes?
- Files exist?
- Paths relative to `sim/` directory?
- Syntax errors in HDL?

### Simulation Issues → Check:
- **Read transcript first:** `python scripts/get_transcript.py`
- Correct simulation time?
- TEST_RESULT markers in testbench?

### Waveform Issues → Check:
- Waveform refreshed? (`python scripts/refresh_waveform.py`)
- Signals added? (`python scripts/add_wave.py`)
- Signal paths without leading `/`?
- Use `list_wave_signals.py` to get exact names

### TCL Errors → Check:
- Use `catch` for error handling
- Forward slashes in paths
- Update `modelsim_socket_server.tcl` if JSON errors occur

---

## Getting Help

If you encounter an issue not listed here:

1. **Check transcript:** `sim/transcript` or `python scripts/get_transcript.py`
2. **Check connection:** `python scripts/connection_check.py`
3. **Test manually in ModelSim:**
   ```tcl
   vlog -work work ../hdl/design/counter.v
   ```
4. **Read full error messages** - ModelSim errors are detailed!