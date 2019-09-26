# --------------------- Global configuration --------------------------

# The name of this program.  This will get used to identify logfiles,
# configuration files and other file outputs.
set program_name pscan

# The base filename for the execution log.  The actual filename will add
# a number after this to make a unique logfile name.
set execution_logbase "pscan"

# This software's version.  Anything set here will be clobbered by the
# makefile when starpacks are built.
set revcode 1.0

# Set the log level.  Known values are:
# debug
# info
# notice
# warn
# error
# critical
# alert
# emergency
set loglevel debug

set root_directory [file dirname $argv0]

package require math::statistics

# ---------------------- Command line parsing -------------------------
package require cmdline
set usage "usage: [file tail $argv0] \[options]"

set options {
    {b.arg "mega" "Board name"}
    {o.arg "pscan" "Output file name base"}
    {n.arg "20" "Number of read cycles"}
    {r.arg "10" "Read rate (Hz)"}
}

try {
    array set params [::cmdline::getoptions argv $options $usage]
} trap {CMDLINE USAGE} {msg o} {
    # Trap the usage signal, print the message, and exit the application.
    # Note: Other errors are not caught and passed through to higher levels!
    puts $msg
    exit 1
}

set output_file_name $params(o).csv

# Create a dictionary to keep track of global state
# State variables:
#   program_name --  Name of this program (for naming the window)
#   program_version -- Version of this program
#   thisos  -- Name of the os this program is running on
#   exelog -- The execution log filename
#   serlog -- The serial output log filename
#   device_character_delay_ms -- Delay between sent characters
set state [dict create \
	       program_name $program_name \
	       program_version $revcode \
	       thisos $tcl_platform(os) \
	       exelog none \
	       serlog none \
	       device_character_delay_ms 100
	  ]

# --------------------- Tools for code modules ------------------------
source [file join $root_directory module_tools.tcl]

# Math tools
source [file join $root_directory jpmath.tcl]

#----------------------------- Set up logger --------------------------

# The logging system will use the console text widget for visual
# logging.

package require logger
source loggerconf.tcl
${log}::info [modinfo logger]

set time_format "%Y-%m-%d %H:%M:%S"

proc source_script {file args} {
    # Execute a tcl script by sourcing it.  Note that this will
    # clobber your existing argument list.
    set argv $::argv
    set argc $::argc
    set ::argv $args
    set ::argc [llength $args]
    set code [catch {uplevel [list source $file]} return]
    set ::argv $argv
    set ::argc $argc
    return -code $code $return
}

proc iterint {start points} {
    # Return a list of increasing integers starting with start with
    # length points
    set count 0
    set intlist [list]
    while {$count < $points} {
	lappend intlist [expr $start + $count]
	incr count
    }
    return $intlist
}

proc dashline {width} {
    # Return a string of dashes of length width
    set dashline ""
    foreach dashchar [iterint 0 $width] {
	append dashline "-"
    }
    return $dashline
}

proc get_time_string {start_time_ms} {
    global time_format
    set time_now_ms [clock milliseconds]
    set time_now_s [expr double($time_now_ms)/1000]
    # time_delta_s is a millisecond-resolution stopwatch started at
    # script execution.  The number is in floating-point seconds.
    set time_delta_ms [expr $time_now_ms - $start_time_ms]
    # set ms_remainder [expr int($time_delta_s * 1000 - int($time_delta_s) * 1000)]
    set ms_remainder [expr $time_delta_ms - int($time_delta_ms / double(1000)) * 1000]
    # Gnuplot can plot timestamps with ms resolution, but not if
    # they're formatted as unix time stamps.  We have to make a
    # timestamp like:
    # 2019-06-29 18:18:15.891
    # ... by tacking milliseconds onto a conventional clock format.
    set time_string [format "%s.%03d" [clock format [expr int($time_now_s)] -format \
					   $time_format] $ms_remainder]
    return $time_string
}

proc lmean  L {
    expr ([join $L +])/[llength $L].
}

proc get_channel_list {dict_list channel} {
    foreach cycle_dict $dict_list {
	lappend channel_list [dict get $cycle_dict $channel pressure]
    }
    return $channel_list
}

# Testing the logger

puts "Current loglevel is: [${log}::currentloglevel] \n"
${log}::info "Trying to log to [dict get $state exelog]"
${log}::info "Known log levels: [logger::levels]"
${log}::info "Known services: [logger::services]"
${log}::debug "Debug message"
${log}::info "Info message"
${log}::warn "Warn message"


source connection.tcl
source boxer.tcl
${log}::debug "Potential connection nodes: [connection::get_potential_aliases]"
foreach alias [connection::get_potential_aliases] {
    if {$params(b) == "whitfield"} {
	set channel [connection::is_available $alias "230400,n,8,1"]
    } else {
	set channel [connection::is_available $alias "38400,n,8,1"]
    }

    if { ![string equal $channel false] } {
	# This is a viable connection alias, and it's now going
	# through a reset.  The USB connection asserts DTR after the
	# channel is configured, resetting the part.  We have to wait
	# for the bootloader to time out and for rebooting to happen
	# before we can send commands.
	after 3000

	${log}::debug "Alias $alias can be configured"
	dict set state channel $channel
	dict set state alias $alias
	# Ask for identity
	boxer::sendcmd $channel "*idn?"
	# Read the response
	try {
	    set data [boxer::readline $channel]
	    ${log}::debug "Response to *idn? was $data"
	    if {[string last "Picarro" $data] >= 0} {
		# We found the string we wanted to find in the response
		${log}::info "Successful connection to boxer running on $params(b) at $alias"
		break
	    } else {
		dict set state channel "none"
		dict set state alias "none"
	    }
	} trap {} {message optdict} {
	    # We couldn't read from the channel -- this is definitely
	    # not a device we want to talk to.
	    dict set state channel "none"
	    dict set state alias "none"
	}
    }
}

if [string equal [dict get $state channel] "none"] {
    ${log}::error "Could not talk to boxer running on $params(b).  Check -b parameter."
    exit
}

try {
    set fid [open $output_file_name w]
    ${log}::info "Opened $output_file_name"
} trap {} {message optdict} {
    puts $message
}

set read_period_ms [expr double(1000)/$params(r)]

# Configure exponential moving average
boxer::sendcmd $channel "prs.alpha 1180"
set return_value [boxer::readline $channel]

# Wait for system to start reading pressures
after 5000

set column_width 10

foreach pressure_channel [iterint 1 8] {
    dict set table_dict $pressure_channel width $column_width
    dict set table_dict $pressure_channel description $pressure_channel
}
dict set table_dict "outlet a" width $column_width
dict set table_dict "outlet a" description "outlet a"

dict set table_dict "outlet b" width $column_width
dict set table_dict "outlet b" description "outlet b"

foreach column [dict keys $table_dict] {
    append format_string "%-*s "
    append file_format_string "%-*s, "
    lappend header_list [dict get $table_dict $column width]
    lappend header_list [dict get $table_dict $column description]
}
set format_string [string trim $format_string]
set file_format_string [string trim $file_format_string ", "]


set header [format $format_string {*}$header_list]

puts ""
puts $header

puts [dashline [string length $header]]


set start_time_ms [clock milliseconds]

foreach read_cycle [iterint 0 $params(n)] {
    set pressure_channels {1 2 3 4 5 6 7 8}
    foreach pressure_channel $pressure_channels {
	boxer::sendcmd $channel "prs.in.raw? $pressure_channel"
	set cycle_start_time_ms [clock milliseconds]
	set return_value [boxer::readline $channel]
	dict set measurement_dict $pressure_channel pressure $return_value
	dict set measurement_dict $pressure_channel time_string [get_time_string $start_time_ms]
	dict set measurement_dict $pressure_channel unix_time_ms [clock milliseconds]
	while {[expr [clock milliseconds] - $cycle_start_time_ms] < $read_period_ms} {
	    after 1
	}
    }
    foreach [list channel_name pressure_channel] [list "outlet a" 1 "outlet b" 2] {
	boxer::sendcmd $channel "prs.out.raw? $pressure_channel"
	set cycle_start_time_ms [clock milliseconds]
	set return_value [boxer::readline $channel]
	dict set measurement_dict $channel_name pressure $return_value
	dict set measurement_dict $channel_name time_string [get_time_string $start_time_ms]
	dict set measurement_dict $channel_name unix_time_ms [clock milliseconds]
	while {[expr [clock milliseconds] - $cycle_start_time_ms] < $read_period_ms} {
	    after 1
	}
    }
    set row_list [list]
    # Create a list of dictionaries for later analysis
    lappend read_cycle_list $measurement_dict
    foreach key [dict keys $table_dict] {
	lappend row_list [dict get $table_dict $key width]
	lappend row_list [dict get $measurement_dict $key pressure]
	
    }
    if {([expr $read_cycle % 10] == 0) && ($read_cycle != 0)} {
	puts ""
	puts $header
	puts [dashline [string length $header]]
    }

    puts [format $format_string {*}$row_list]
    set file_string "[dict get $measurement_dict 1 time_string], "
    append file_string [format $file_format_string {*}$row_list]
    puts $fid $file_string
}
close $fid


set first_dict [lindex $read_cycle_list 0]
set first_time [dict get $first_dict 1 unix_time_ms]

set last_dict [lindex $read_cycle_list end]
set last_time [dict get $last_dict "outlet b" unix_time_ms]
set readings [expr 10 * [llength $read_cycle_list]]
set duration_ms [expr $last_time - $first_time]
set read_rate [expr (double($readings) * 1000) / $duration_ms]
puts "Took $readings readings in $duration_ms ms at [format "%0.2f" $read_rate] Hz"

unset table_dict
unset format_string
unset header_list
set column_width 20

dict set table_dict "channel" width $column_width
dict set table_dict "channel" description "Channel"

dict set table_dict "mean" width $column_width
dict set table_dict "mean" description "Mean"

dict set table_dict "std" width $column_width
dict set table_dict "std" description "Std Dev"


# Report mean and standard deviation
foreach column [dict keys $table_dict] {
    append format_string "%-*s "
    lappend header_list [dict get $table_dict $column width]
    lappend header_list [dict get $table_dict $column description]
}
set format_string [string trim $format_string]
set header [format $format_string {*}$header_list]

puts ""
puts $header

puts [dashline [string length $header]]


set channel_list [list 1 2 3 4 5 6 7 8 "outlet a" "outlet b"]
foreach channel $channel_list {
    unset row_list
    lappend row_list $column_width
    lappend row_list $channel
    lappend row_list $column_width
    lappend row_list [format "%0.0f" \
			  [math::statistics::mean [get_channel_list $read_cycle_list $channel]]]
    lappend row_list $column_width
    lappend row_list [format "%0.0f" \
			  [math::statistics::pstdev [get_channel_list $read_cycle_list $channel]]]
    puts [format $format_string {*}$row_list]
}

package require Tk
package require Plotchart

canvas .c -background white -width 1000 -height 600
pack .c -fill both
tkwait visibility .c
set data_list [get_channel_list $read_cycle_list 1]
set number_of_points [llength $data_list]
set plot_min [math::statistics::min $data_list]
set plot_max [math::statistics::max $data_list]
set plot_ytic [expr int(($plot_max - $plot_min)/10)]
set plot_xtic [expr int($number_of_points / 10)]
set s [Plotchart::createXYPlot .c [list 0 [llength $data_list] $plot_xtic] \
	   [list [expr $plot_min - $plot_ytic] [expr $plot_max + $plot_ytic] $plot_ytic]]
foreach x [iterint 0 [llength $data_list]] y $data_list {
    $s plot series1 $x $y
}








