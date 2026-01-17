# Advanced Waveform Control

This document provides detailed guidance for advanced waveform viewing and manipulation in ModelSim.

## Waveform Zoom

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

## Signal Display Format

Change signal display formats between binary, decimal, hexadecimal, and octal.

### Recommended Workflow (Two-Step Process)

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

## Analog Wave Display

Display signals as analog waveforms with auto-scaled min/max values for better visualization of value changes.

**Usage with add_wave_analog.py:**

```bash
# Add analog waveform (radix REQUIRED)
python $SKILL/scripts/add_wave_analog.py "counter_tb/count" --radix unsigned
# Register [7:0] → Auto-scales to 0-255

python $SKILL/scripts/add_wave_analog.py "adc_tb/sample" --radix signed
# Register [11:0] → Auto-scales to -2048 to 2047

# With custom height
python $SKILL/scripts/add_wave_analog.py "pwm_tb/duty" --radix unsigned --height 120
```

**Use cases:**
- Visualize counter values as analog signals
- Display PWM duty cycle changes
- Show ADC/DAC signal levels
- Analyze signal transitions visually

**Important Notes:**
- The `--radix` parameter is **required** (signed or unsigned)
- Auto-scaling: Script automatically calculates min/max from bit width
- Only signals with explicit bit width (e.g., `Register [7:0]`, `Wire [15:0]`) are supported
- Signals without bit width (`Integer`, `Real`) are **not supported**
- Analog signals are added with `_analog` suffix label to avoid conflicts
- Default height is 80 pixels (customizable with `--height` parameter)
- You can have both digital and analog views of the same signal simultaneously