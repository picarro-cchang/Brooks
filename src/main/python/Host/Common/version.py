"""
Copyright 2012 Picarro Inc.

A non-release version string containing enough information to track
the work back to the originating revision.
"""

import subprocess
import sys


def versionString():
    """
    We purposely don't cache the non-official version since it could
    change during active development. This should never be invoked
    from a compiled (py2exe) app since it won't be in a repository.
    """

    ver = ""

    if 'rpdb2' in sys.modules.keys():
        # Popen is is not thread safe and is known to deadlock if Popen is
        # is used too much.  I have found that the rpdb2 debugger causes
        # Popen to deadlock more often and it seems to always deadlock
        # here if I run rpdb2 on Driver.py.
        #
        # If rpdb2 is loaded skip this call to git so the code will run.
        #
        ver = "rpdb2 loaded, no version"
    else:
        # This doesn't work with Linux (it's git and not git.exe)
        # and you probably want the -C option to define the repository path.
        #
        p = subprocess.Popen(['git.exe', 'log', '-1',
                            '--pretty=format:%H'], stdout=subprocess.PIPE)

        ver = "Internal (%s)" % p.communicate()[0]

    return ver