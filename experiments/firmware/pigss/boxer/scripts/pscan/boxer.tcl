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
    }

    proc readline {channel} {
	set raw_data [connection::wait_for_data $channel 5000]
	set data [string trim $raw_data]
	return $data
    }
}
