#!/usr/bin/python
#
# FILE:  
#   usb.py
#
# DESCRIPTION:                                                
#   Host version informatio
#                                                             
# SEE ALSO:                                             
#   Specify any related information.                   
#                                                             
# HISTORY:
#   07-Jan-2009  sze  Version 0.0.1 Copied from silverstone project
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved 
#                                                            
HOST_MAJOR_VERSION = 0
HOST_MINOR_VERSION = 0
HOST_INTERNAL_VERSION = "3"

def versionString():
    if HOST_INTERNAL_VERSION in [0, "0"]:
        return "%d.%d" % (HOST_MAJOR_VERSION,HOST_MINOR_VERSION)
    else:
        return "%d.%d.%s" % (HOST_MAJOR_VERSION,HOST_MINOR_VERSION,str(HOST_INTERNAL_VERSION))
