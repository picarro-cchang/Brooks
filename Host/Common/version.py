"""
Copyright 2012 Picarro Inc.

A non-release version string containing enough information to track
the work back to the originating revision.
"""

import subprocess
import cStringIO


def versionString():
    """
    We purposely don't cache the non-official version since it could
    change during active development. This should never be invoked
    from a compiled (py2exe) app since it won't be in a repository.
    """

    revisionId = cStringIO.StringIO()
    subprocess.Popen(['bzr.exe', 'version-info', '--custom',
                      '--template="{revision_id}"'], stdout=revisionId).wait()

    ver = "Internal (%s)" % revisionId.getvalue()
    revisionId.close()

    return ver
