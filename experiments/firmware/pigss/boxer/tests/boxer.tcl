namespace eval boxer {
    # Procedures and variables unique to the boxer project
    
    proc init {channel} {
	# Send a carriage return to reset the command state
	puts -nonewline $channel "\r"
	after 100
    }

    proc sendcmd {channel data} {
	global state
	set payload "${data}\r"
	puts -nonewline $channel $payload
	# Wait for the return
	after 500
    }

    proc readline {channel} {
	set data [chan gets $channel]
	return $data
    }
}
