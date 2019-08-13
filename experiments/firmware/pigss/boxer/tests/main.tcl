# --------------------- Global configuration --------------------------

# The name of this program.  This will get used to identify logfiles,
# configuration files and other file outputs.
set program_name unotest


# The base filename for the execution log.  The actual filename will add
# a number after this to make a unique logfile name.
set execution_logbase "unotest"

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

# Set verbosity to print output when a test passes
tcltest::configure -verbose {body pass start error}

source connection.tcl
source boxer.tcl
${log}::debug "Potential connection nodes: [connection::get_potential_aliases]"
foreach alias [connection::get_potential_aliases] {
    set channel [connection::is_available $alias "38400,n,8,1"]
    if { ![string equal $channel false] } {
	# This is a viable connection alias, and it's now going
	# through a reset.  The USB connection asserts DTR after the
	# channel is configured, resetting the part.  We have to wait
	# for the bootloader to time out and for rebooting to happen
	# before we can send commands.
	after 5000
	${log}::debug "Alias $alias can be configured"
	dict set state channel $channel
	dict set state alias $alias
	# Set up snowball to accept commands
	# boxer::init $channel
	# Ask for identity
	boxer::sendcmd $channel "*idn?"
	# Read the response
	try {
	    set data [boxer::readline $channel]
	    ${log}::debug "Response to *idn? was $data"
	    if {[string last "Picarro" $data] >= 0} {
		# We found the string we wanted to find in the response
		${log}::info "Successful connection to Boxer at $alias"
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
    ${log}::error "Did not find a connected Boxer"
    exit
}

tcltest::runAllTests



