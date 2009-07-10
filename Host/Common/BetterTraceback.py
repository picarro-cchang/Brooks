#!/usr/bin/python
#
# File Name: BetterTraceback.py
# Purpose:
#   This file contains a better traceback routine that can be used to print out
#   full stack frame information.
#
# File History:
# 05-07-25 russ  Created (code taken from online cookbook example)
# 06-08-23 russ  get_advanced_traceback as base/usable call; changed exc format
# 06-08-30 russ  Added StackSkipCount options

"""This file contains a better traceback routine that can be used to print out
full stack frame information.

It is a file intended for debugging purposes.
"""

import sys, traceback

def get_advanced_traceback(StackSkipCount = 0):
    """Returns a string with advanced traceback information.

    Info included is:
     - the usal traceback info
     - a listing of all the local variables in each stack frame

     If StackSkipCount > 0, the advanced traceback info will skip that number
     of stack frames in its report (but the basic traceback will still include
     the layers).
     """
    tb = sys.exc_info()[2]
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    if StackSkipCount:
        stack = stack[:-abs(StackSkipCount)]
    buf = ""
    try:
        buf += "******************************************************\n"
        buf += "**** NORMAL TRACEBACK\n"
        buf += "******************************************************\n"
        buf += traceback.format_exc()
        buf += "******************************************************\n"
        buf += "**** STACK DATA  (locals by frame, innermost last)\n"
        buf += "******************************************************\n"
        for frame in stack:
            buf += "------\n"
            buf += "Frame %s in %s at line %s\n" % (frame.f_code.co_name,
                                                    frame.f_code.co_filename,
                                                    frame.f_lineno)
            for key, value in frame.f_locals.items():
                buf += "  %25s = " % key
                #We have to be careful not to cause a new error in our error
                #printer! Calling str() on an unknown object could cause an
                #error we don't want.
                try:
                    buf += "%s\n" % value
                except:
                    buf += "<ERROR WHILE PRINTING VALUE>\n"
    except:
        pass
    return buf

def print_exc_plus(StackSkipCount = 0):
    """Same as get_advanced_traceback, but prints the info."""
    print get_advanced_traceback(StackSkipCount)

if __name__ == '__main__':
    #A simplistic demonstration of the kind of problem this approach can help
    #with. Basically, we have a simple function which manipulates all the
    #strings in a list. The function doesn't do any error checking, so when
    #we pass a list which contains something other than strings, we get an
    #error. Figuring out what bad data caused the error is easier with our
    #new function.

    data = ["1", "2", 3, "4"] #Typo: We 'forget' the quotes on data[2]
    def pad4(seq):
        """
        Pad each string in seq with zeros, to four places. Note there
        is no reason to actually write this function, Python already
        does this sort of thing much better.
        Just an example.
        """
        return_value = []
        for thing in seq:
            return_value.append("0" * (4 - len(thing)) + thing)
        return return_value

    #First, show the information we get from a normal traceback.print_exc().
    try:
        pad4(data)
    except:
        traceback.print_exc()
    print
    print "----------------"
    print

    #Now with our new function. Note how easy it is to see the bad data that
    #caused the problem. The variable 'thing' has the value 3, so we know
    #that the TypeError we got was because of that. A quick look at the
    #value for 'data' shows us we simply forgot the quotes on that item.
    try:
        pad4(data)
    except:
        print_exc_plus()
