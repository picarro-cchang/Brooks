"""
Copyright 2012 Picarro Inc.

A non-release version string containing enough information to track
the work back to the originating revision.
"""

import sys
import os
# If we are using python 2.x on Linux, use the subprocess32
# module which has many bug fixes and can prevent
# subprocess deadlocks.
#
if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

def versionString():
    """
    We purposely don't cache the non-official version since it could
    change during active development. This should never be invoked
    from a compiled (py2exe) app since it won't be in a repository.
    """

    ver = ""

    if os.name == 'posix':
        ver = subprocess.check_output(['/usr/bin/git','log','-1','--pretty=format:%H'])
        ver = "Internal (%s)" % ver
    else:
        p = subprocess.Popen(['git', 'log', '-1',
                            '--pretty=format:%H'], stdout=subprocess.PIPE)
        ver = "Internal (%s)" % p.communicate()[0]

    return ver