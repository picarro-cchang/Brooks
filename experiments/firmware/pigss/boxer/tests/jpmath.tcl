namespace eval jpmath {

    proc bin2dec bin {
	#returns integer equivalent of $bin 
	set res 0
	if {$bin == 0} {
	    return 0
	} elseif {[string match -* $bin]} {
	    set sign -
	    set bin [string range $bin[set bin {}] 1 end]
	} else {
	    set sign {}
	}
	foreach i [split $bin {}] {
	    set res [expr {$res*2+$i}]
	}
	return $sign$res
    }

}
