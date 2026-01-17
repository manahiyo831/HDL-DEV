# Examples and Templates

This document provides complete examples and templates for HDL development.

## Example 1: Counter

Basic 8-bit counter with enable and reset.

- Design: [assets/examples/counter.v](../assets/examples/counter.v)
- Testbench: [assets/examples/counter_tb.v](../assets/examples/counter_tb.v)

**Features demonstrated:**
- Clock generation
- Reset sequence
- Enable control
- TEST_RESULT: markers
- Watchdog timer

## Example 2: Pulse Generator (1ms)

Generates 1 pulse every 1ms with 1MHz clock input.

- Design: [assets/examples/pulse_gen_1ms.v](../assets/examples/pulse_gen_1ms.v)
- Testbench: [assets/examples/pulse_gen_1ms_tb.v](../assets/examples/pulse_gen_1ms_tb.v)

**Features demonstrated:**
- Parameter-based timing (COUNT_MAX = 1000-1)
- Pulse interval verification with tolerance (±1%)
- Multiple pulse detection (3 pulses)
- Real-world timing constraints (1MHz clock, 1ms period)

## Templates

### Design Specification Template

[assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md](../assets/templates/HDL_DESIGN_SPECIFICATION_TEMPLATE.md)

Comprehensive HDL design specification template for complex designs:
- Interface and signal definitions
- Timing and protocol specifications
- State machine documentation
- Register maps
- Verification scenarios
- **Note:** Fill in only relevant sections; omit sections that don't apply

### Testbench Template

[assets/templates/basic_testbench_template.v](../assets/templates/basic_testbench_template.v)

Complete testbench skeleton with:
- Clock generation
- Test case structure
- TEST_RESULT: markers
- Watchdog timer
- Best practices