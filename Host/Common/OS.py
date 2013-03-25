# Copyright 2012 Picarro Inc.

"""
Enhanced version of routines found in standard os module.
"""

import os
import contextlib


@contextlib.contextmanager
def chdir(d):
    """
    Use as part of a 'with' statement to perform some operations in
    the context of the specified directory without having to manually
    restore the original path.
    """

    origDir = os.getcwd()

    try:
        os.chdir(d)
        yield d

    finally:
        os.chdir(origDir)
