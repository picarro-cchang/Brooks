"""
Copyright 2013 Picarro Inc.

Custom path manipulation methods not provided by os.path.
"""

import os.path


def splitToDirs(path):
    """
    Unlike os.path.split() which returns (tail, head), this routine returns
    a list with each directory as its own element.
    """

    dirs = []

    while True:
        path, folder = os.path.split(path)

        if folder != '':
            dirs.append(folder)
        else:
            if path != '':
                dirs.append(path)

            break

    dirs.reverse()
    return dirs
