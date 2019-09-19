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

# ---------------------- Command line parsing -------------------------
package require cmdline
set usage "usage: [file tail $argv0] \[options]"

set options {
    {b.arg "mega" "Board name"}
    {o.arg "pscan" "Output file name base"}
    {n.arg "20" "Number of read cycles"}
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
					   "%Y-%m-%d %H:%M:%S"] $ms_remainder]
    return $time_string
}

# Testing the logger

puts "Current loglevel is: [${log}::currentloglevel] \n"
${log}::info "Trying to log to [dict get $state exelog]"
${log}::info "Known log levels: [logger::levels]"
${log}::info "Known services: [logger::services]"
${log}::debug "Debug message"
${log}::info "Info message"
${log}::warn "Warn message"

############################## tcltest ###############################
package require tcltest
tcltest::configure -singleproc true

set skiplist [list]
# lappend skiplist chanset.*
# lappend skiplist slotid*
# lappend skiplist slotid?*
# lappend skiplist standby*

tcltest::configure -skip $skiplist

# Only run the channel locations test.  Comment this out to run all
# tests.
# tcltest::configure -file "channel_locations.test"

# Set verbosity to print output when a test passes
tcltest::configure -verbose {body pass start error}

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
	set return_value [boxer::readline $channel]
	dict set measurement_dict $pressure_channel pressure $return_value
	dict set measurement_dict $pressure_channel time_string [get_time_string $start_time_ms]
    }
    foreach [list channel_name pressure_channel] [list "outlet a" 1 "outlet b" 2] {
	boxer::sendcmd $channel "prs.out.raw? $pressure_channel"
	set return_value [boxer::readline $channel]
	dict set measurement_dict $channel_name pressure $return_value
	dict set measurement_dict $channel_name time_string [get_time_string $start_time_ms]
    }
    set row_list [list]
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








