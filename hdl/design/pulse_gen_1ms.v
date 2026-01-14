// ============================================================================
// Module: pulse_gen_1ms
// Description: Generates a 1-cycle pulse every 1ms with 1MHz clock
// ============================================================================
// Clock: 1MHz (period = 1us)
// Reset: Active high (positive logic)
// Output: 1 pulse every 1ms (1000 clock cycles)
// ============================================================================

module pulse_gen_1ms (
    input  wire clk,        // 1MHz clock
    input  wire rst,        // Reset (active high)
    output reg  pulse       // Output pulse (1 cycle every 1ms)
);

    // Parameters
    parameter COUNT_MAX = 1000 - 1;  // Count from 0 to 999 (1000 cycles = 1ms)

    // Counter width calculation: ceil(log2(1000)) = 10 bits
    reg [9:0] counter;

    // Counter and pulse generation
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            counter <= 10'd0;
            pulse   <= 1'b0;
        end else begin
            if (counter == COUNT_MAX) begin
                counter <= 10'd0;
                pulse   <= 1'b1;      // Generate pulse
            end else begin
                counter <= counter + 1'b1;
                pulse   <= 1'b0;      // Clear pulse
            end
        end
    end

endmodule
