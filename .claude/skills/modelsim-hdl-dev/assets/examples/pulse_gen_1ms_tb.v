// ============================================================================
// Testbench: pulse_gen_1ms_tb
// Description: Verify pulse_gen_1ms module
// ============================================================================
// Verification Strategy:
// 1. Detect 3 consecutive pulses
// 2. Measure interval between pulses
// 3. Verify interval is 1000 cycles ± 1%
// ============================================================================

`timescale 1ns/1ps

module pulse_gen_1ms_tb;

    // Clock period: 1MHz = 1us = 1000ns
    parameter CLK_PERIOD = 1000;
    parameter EXPECTED_INTERVAL = 1000;  // 1000 cycles = 1ms
    parameter TOLERANCE = 10;             // ±1% = ±10 cycles

    // DUT signals
    reg  clk;
    reg  rst;
    wire pulse;

    // Test variables
    integer pulse_count;
    integer last_pulse_time;
    integer current_pulse_time;
    integer interval;
    integer cycle_count;
    reg test_passed;

    // Instantiate DUT
    pulse_gen_1ms dut (
        .clk(clk),
        .rst(rst),
        .pulse(pulse)
    );

    // Clock generation: 1MHz (period = 1us = 1000ns)
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // Main test procedure
    initial begin
        $display("=== Pulse Generator (1ms) Test Start ===");
        $display("Clock: 1MHz (period = %0d ns)", CLK_PERIOD);
        $display("Expected pulse interval: %0d cycles", EXPECTED_INTERVAL);
        $display("Tolerance: ±%0d cycles (±1%%)", TOLERANCE);
        $display("");

        // Initialize
        rst = 1;
        pulse_count = 0;
        last_pulse_time = 0;
        current_pulse_time = 0;
        cycle_count = 0;
        test_passed = 1;

        // Reset pulse
        repeat(5) @(posedge clk);
        rst = 0;
        $display("[%0t ns] Reset released", $time);

        // Wait for and verify 3 pulses
        while (pulse_count < 3) begin
            @(posedge clk);
            cycle_count = cycle_count + 1;

            // Detect pulse rising edge
            if (pulse == 1'b1) begin
                current_pulse_time = cycle_count;
                pulse_count = pulse_count + 1;

                if (pulse_count == 1) begin
                    $display("[%0t ns] Pulse #%0d detected at cycle %0d",
                             $time, pulse_count, current_pulse_time);
                end else begin
                    interval = current_pulse_time - last_pulse_time;
                    $display("[%0t ns] Pulse #%0d detected at cycle %0d",
                             $time, pulse_count, current_pulse_time);
                    $display("  Interval: %0d cycles (expected: %0d ± %0d)",
                             interval, EXPECTED_INTERVAL, TOLERANCE);

                    // Check interval
                    if (interval < (EXPECTED_INTERVAL - TOLERANCE) ||
                        interval > (EXPECTED_INTERVAL + TOLERANCE)) begin
                        $display("  ERROR: Interval out of range!");
                        test_passed = 0;
                    end else begin
                        $display("  OK: Interval within tolerance");
                    end
                end

                last_pulse_time = current_pulse_time;

                // Wait for pulse to go low
                @(posedge clk);
            end
        end

        $display("");
        $display("=== Test Complete ===");
        $display("Total pulses detected: %0d", pulse_count);

        // Display result with TEST_RESULT marker
        if (test_passed && pulse_count == 3) begin
            $display("TEST_RESULT: PASS - All pulses detected with correct timing");
        end else begin
            $display("TEST_RESULT: FAIL - Timing errors or incorrect pulse count");
        end

        $finish;
    end

    // Watchdog timer: 5ms timeout (5000 cycles)
    initial begin
        #(CLK_PERIOD * 5000);
        $display("");
        $display("TEST_RESULT: FAIL - Timeout (expected 3 pulses within 5ms)");
        $finish;
    end

    // Optional: Dump waveform for viewing
    initial begin
        $dumpfile("pulse_gen_1ms.vcd");
        $dumpvars(0, pulse_gen_1ms_tb);
    end

endmodule
