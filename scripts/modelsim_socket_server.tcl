# ModelSim TCL Socket Server
# Allows Python clients to send commands to a running ModelSim instance
# Author: Claude Code
# Date: 2026-01-14

# Global variables (initialize to avoid undefined variable errors)
if {![info exists server_socket]} {
    set server_socket ""
}
if {![info exists server_port]} {
    set server_port 12345
}
if {![info exists client_sockets]} {
    set client_sockets {}
}
if {![info exists design_files_global]} {
    set design_files_global {}
}
if {![info exists testbench_file_global]} {
    set testbench_file_global ""
}
if {![info exists top_module_global]} {
    set top_module_global ""
}

# Start the socket server
proc start_socket_server {{port 12345}} {
    global server_socket server_port
    set server_port $port

    # Close existing server if any
    if {[info exists server_socket] && $server_socket != ""} {
        catch {close $server_socket}
    }

    # Create server socket
    if {[catch {socket -server handle_client $port} server_socket]} {
        echo "ERROR: Failed to start socket server on port $port: $server_socket"
        return 0
    }

    echo "========================================"
    echo "Socket Server Started"
    echo "========================================"
    echo "Port: $port"
    echo "Waiting for Python client connections..."
    echo "Available commands:"
    echo "  - ping: Check connection"
    echo "  - recompile: Recompile design files"
    echo "  - restart: Restart simulation"
    echo "  - run: Run simulation for specified time"
    echo "  - wave_refresh: Refresh waveform display"
    echo "  - exec_tcl: Execute arbitrary TCL command"
    echo "  - shutdown: Stop server and close ModelSim"
    echo "========================================"

    return 1
}

# Handle new client connection
proc handle_client {sock addr port} {
    global client_sockets

    echo "Client connected from $addr:$port"
    lappend client_sockets $sock

    # Configure socket
    fconfigure $sock -buffering line -blocking 0 -encoding utf-8
    fileevent $sock readable [list handle_command $sock]
}

# Handle commands from client
proc handle_command {sock} {
    global client_sockets

    # Check if socket is still readable
    if {[eof $sock]} {
        echo "Client disconnected"
        catch {close $sock}
        set idx [lsearch $client_sockets $sock]
        if {$idx >= 0} {
            set client_sockets [lreplace $client_sockets $idx $idx]
        }
        return
    }

    # Read command from socket
    if {[catch {gets $sock line} result]} {
        echo "ERROR: Failed to read from socket: $result"
        return
    }

    # Skip empty lines
    if {$line == ""} {
        return
    }

    # Parse JSON command (simplified - expecting JSON on one line)
    if {[catch {parse_json_command $line} cmd_result]} {
        send_response $sock [dict create \
            success false \
            message "Failed to parse command: $cmd_result" \
            output "" \
            errors [list $cmd_result] \
            warnings [list]]
        return
    }

    # Extract command and params
    set command [dict get $cmd_result command]
    set params [dict get $cmd_result params]

    echo "Received command: $command"

    # Execute command
    set response [execute_command $command $params]

    # Send response back to client
    send_response $sock $response
}

# Parse JSON-like command (simplified parser)
proc parse_json_command {json_str} {
    # Remove outer braces and whitespace
    set json_str [string trim $json_str]
    set json_str [string range $json_str 1 end-1]

    # Initialize result dict
    set result [dict create command "" params [dict create]]

    # Simple state machine to parse JSON
    set in_string 0
    set current_key ""
    set current_value ""
    set depth 0
    set i 0

    # Look for "command" field
    if {[regexp {"command"\s*:\s*"([^"]+)"} $json_str -> cmd_value]} {
        dict set result command $cmd_value
    }

    # Look for "params" object
    if {[regexp {"params"\s*:\s*\{([^\}]*)\}} $json_str -> params_str]} {
        # Parse params as key-value pairs
        set params_dict [dict create]

        # Extract design_files array
        if {[regexp {"design_files"\s*:\s*\[([^\]]*)\]} $params_str -> files_str]} {
            set files_list {}
            foreach file_match [regexp -all -inline {"([^"]+)"} $files_str] {
                if {[string index $file_match 0] == "\""} {
                    lappend files_list [string range $file_match 1 end-1]
                }
            }
            dict set params_dict design_files $files_list
        }

        # Extract testbench_file
        if {[regexp {"testbench_file"\s*:\s*"([^"]+)"} $params_str -> tb_file]} {
            dict set params_dict testbench_file $tb_file
        }

        # Extract time
        if {[regexp {"time"\s*:\s*"([^"]+)"} $params_str -> time_val]} {
            dict set params_dict time $time_val
        }

        # Extract tcl_code
        if {[regexp {"tcl_code"\s*:\s*"([^"]+)"} $params_str -> tcl_val]} {
            dict set params_dict tcl_code $tcl_val
        }

        dict set result params $params_dict
    }

    return $result
}

# Execute command and return response
proc execute_command {command params} {
    switch $command {
        "ping" {
            return [cmd_ping $params]
        }
        "recompile" {
            return [cmd_recompile $params]
        }
        "restart" {
            return [cmd_restart $params]
        }
        "run" {
            return [cmd_run $params]
        }
        "wave_refresh" {
            return [cmd_wave_refresh $params]
        }
        "exec_tcl" {
            return [cmd_exec_tcl $params]
        }
        "get_wave_geometry" {
            return [cmd_get_wave_geometry $params]
        }
        "shutdown" {
            return [cmd_shutdown $params]
        }
        default {
            return [dict create \
                success false \
                message "Unknown command: $command" \
                output "" \
                errors [list "Unknown command: $command"] \
                warnings [list]]
        }
    }
}

# Send response to client as JSON
proc send_response {sock response} {
    # Convert dict to JSON
    set json [dict_to_json $response]

    # Send JSON response
    if {[catch {puts $sock $json} err]} {
        echo "ERROR: Failed to send response: $err"
    }

    # Flush output
    if {[catch {flush $sock} err]} {
        echo "ERROR: Failed to flush socket: $err"
    }
}

# Convert TCL dict to JSON string
proc dict_to_json {d} {
    set parts {}
    dict for {key value} $d {
        # Try to get list length, catch errors for invalid list formats
        if {[catch {llength $value} len]} {
            # Invalid list format (e.g., contains unescaped colons)
            # Treat as plain string
            lappend parts "\"$key\": \"[escape_json_string $value]\""
        } elseif {$len > 1} {
            # Valid list with multiple elements (arrays in JSON)
            set items {}
            foreach item $value {
                lappend items "\"[escape_json_string $item]\""
            }
            lappend parts "\"$key\": \[[join $items ", "]\]"
        } elseif {$len == 0} {
            # Empty list
            lappend parts "\"$key\": \[\]"
        } elseif {$value != "" && [string is boolean -strict $value]} {
            # Boolean value
            lappend parts "\"$key\": [expr {$value ? "true" : "false"}]"
        } else {
            # String (including single-element "lists")
            lappend parts "\"$key\": \"[escape_json_string $value]\""
        }
    }
    return "\{[join $parts ", "]\}"
}

# Escape special characters in JSON strings
proc escape_json_string {str} {
    set str [string map {"\\" "\\\\" "\"" "\\\"" "\n" "\\n" "\r" "\\r" "\t" "\\t"} $str]
    return $str
}

# ============================================================
# Command Implementations
# ============================================================

# Ping command - check if server is alive
proc cmd_ping {params} {
    return [dict create \
        success true \
        message "pong" \
        output "Server is alive" \
        errors [list] \
        warnings [list]]
}

# Recompile command - recompile design and testbench files
proc cmd_recompile {params} {
    global design_files_global testbench_file_global

    # Extract parameters
    if {![dict exists $params design_files]} {
        return [dict create \
            success false \
            message "Missing design_files parameter" \
            output "" \
            errors [list "Missing design_files parameter"] \
            warnings [list]]
    }

    set design_files [dict get $params design_files]
    set testbench_file ""
    if {[dict exists $params testbench_file]} {
        set testbench_file [dict get $params testbench_file]
    }

    # Store for later use
    set design_files_global $design_files
    set testbench_file_global $testbench_file

    set output ""
    set errors {}
    set warnings {}

    # Compile design files
    echo "Recompiling design files..."
    foreach file $design_files {
        if {[catch {vlog -work work $file} result]} {
            lappend errors "Design compilation failed: $file"
            append output "ERROR: $result\n"
            return [dict create \
                success false \
                message "Design compilation failed" \
                output $output \
                errors $errors \
                warnings $warnings]
        }
        append output "Compiled: $file\n"
    }

    # Compile testbench file
    if {$testbench_file != ""} {
        echo "Recompiling testbench..."
        if {[catch {vlog -work work $testbench_file} result]} {
            lappend errors "Testbench compilation failed"
            append output "ERROR: $result\n"
            return [dict create \
                success false \
                message "Testbench compilation failed" \
                output $output \
                errors $errors \
                warnings $warnings]
        }
        append output "Compiled: $testbench_file\n"
    }

    echo "Compilation successful"
    return [dict create \
        success true \
        message "Compilation successful" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Restart command - restart simulation
proc cmd_restart {params} {
    set output ""
    set errors {}
    set warnings {}

    echo "Restarting simulation..."
    if {[catch {restart -f} result]} {
        lappend errors "Restart failed: $result"
        return [dict create \
            success false \
            message "Restart failed" \
            output $result \
            errors $errors \
            warnings $warnings]
    }

    set output "Simulation restarted\n"
    echo "Simulation restarted"

    return [dict create \
        success true \
        message "Simulation restarted" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Run command - run simulation for specified time
proc cmd_run {params} {
    set output ""
    set errors {}
    set warnings {}

    # Extract time parameter
    if {![dict exists $params time]} {
        return [dict create \
            success false \
            message "Missing time parameter" \
            output "" \
            errors [list "Missing time parameter"] \
            warnings [list]]
    }

    set time [dict get $params time]

    echo "Running simulation for $time..."
    if {[catch {run $time} result]} {
        lappend errors "Simulation run failed: $result"
        return [dict create \
            success false \
            message "Simulation run failed" \
            output $result \
            errors $errors \
            warnings $warnings]
    }

    set output "Simulation ran for $time\n"
    echo "Simulation completed"

    return [dict create \
        success true \
        message "Simulation completed" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Wave refresh command - refresh and zoom waveform
proc cmd_wave_refresh {params} {
    set output ""
    set errors {}
    set warnings {}

    echo "Refreshing waveform..."

    # Zoom to full range
    if {[catch {wave zoom full} result]} {
        lappend warnings "Wave zoom failed: $result"
    } else {
        append output "Waveform zoomed to full range\n"
    }

    # Bring wave window to front
    if {[catch {view wave} result]} {
        lappend warnings "View wave failed: $result"
    }

    if {[catch {raise .main_pane.wave} result]} {
        lappend warnings "Raise wave window failed: $result"
    } else {
        append output "Wave window brought to front\n"
    }

    echo "Waveform refreshed"

    return [dict create \
        success true \
        message "Waveform refreshed" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Execute TCL command
proc cmd_exec_tcl {params} {
    set output ""
    set errors {}
    set warnings {}

    # Extract tcl_code parameter
    if {![dict exists $params tcl_code]} {
        return [dict create \
            success false \
            message "Missing tcl_code parameter" \
            output "" \
            errors [list "Missing tcl_code parameter"] \
            warnings [list]]
    }

    set tcl_code [dict get $params tcl_code]

    echo "Executing TCL: $tcl_code"
    if {[catch {eval $tcl_code} result]} {
        lappend errors "TCL execution failed: $result"
        return [dict create \
            success false \
            message "TCL execution failed" \
            output $result \
            errors $errors \
            warnings $warnings]
    }

    set output $result
    echo "TCL executed successfully"

    return [dict create \
        success true \
        message "TCL executed successfully" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Shutdown command - close server and quit ModelSim
proc cmd_shutdown {params} {
    global server_socket client_sockets

    echo "Shutting down server..."

    # Close all client connections
    foreach sock $client_sockets {
        catch {close $sock}
    }
    set client_sockets {}

    # Close server socket
    if {$server_socket != ""} {
        catch {close $server_socket}
        set server_socket ""
    }

    echo "Server stopped"

    # Note: We don't actually quit ModelSim here
    # User can do that manually or send "exec_tcl" with "quit -f"

    return [dict create \
        success true \
        message "Server stopped" \
        output "Server has been stopped. ModelSim is still running." \
        errors [list] \
        warnings [list]]
}

# Get wave window geometry command
proc cmd_get_wave_geometry {params} {
    set output ""
    set errors {}
    set warnings {}

    echo "Getting wave window geometry..."

    # Get waveform display area geometry (not the entire wave window)
    # .main_pane.wave.interior.cs.body.pw.wf is the actual waveform display area
    if {[catch {winfo geometry .main_pane.wave.interior.cs.body.pw.wf} geometry]} {
        lappend errors "Failed to get wave geometry: $geometry"
        return [dict create \
            success false \
            message "Failed to get wave window geometry" \
            output $geometry \
            errors $errors \
            warnings $warnings]
    }

    set output $geometry
    echo "Wave window geometry: $geometry"

    return [dict create \
        success true \
        message "Wave window geometry retrieved" \
        output $output \
        errors $errors \
        warnings $warnings]
}

# Utility: Stop server
proc stop_socket_server {} {
    global server_socket client_sockets

    echo "Stopping socket server..."

    # Close all client connections
    foreach sock $client_sockets {
        catch {close $sock}
    }
    set client_sockets {}

    # Close server socket
    if {$server_socket != ""} {
        catch {close $server_socket}
        set server_socket ""
    }

    echo "Socket server stopped"
}

# Auto-start server when this file is sourced (optional)
# Uncomment the next line to start server automatically
# start_socket_server 12345
