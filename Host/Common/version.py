"""
Copyright 2012 Picarro Inc.

A non-release version string containing enough information to track
the work back to the originating revision.
"""

import subprocess


def versionString():
    """
    We purposely don't cache the non-official version since it could
    change during active development. This should never be invoked
    from a compiled (py2exe) app since it won't be in a repository.
    """

    p = subprocess.Popen(['git.exe', 'log', '-1',
                          '--pretty=format:%H'], stdout=subprocess.PIPE)

    ver = "Internal (%s)" % p.communicate()[0]

    return ver
