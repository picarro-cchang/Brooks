"""
Copyright 2013 Picarro Inc

Tools to load machine-dependent/global constants for our tools.
"""

from __future__ import with_statement

import os.path

#pylint: disable=F0401
try:
    import simplejson as json
except ImportError:
    import json
#pylint: enable=F0401


class Constants(dict):

    def __init__(self):
        dict.__init__(self)

        localFile = os.path.join(os.path.dirname(__file__), 'local.json')

        with open(localFile, 'r') as localFp:
            self.update(json.load(localFp))

        # Constants specific to Picarro that are not a function of the
        # user's installation.
        self.update({'REPO_BASE': 's:/repository/software',
                     'CONFIG_BASE': 's:/CRDSRepositoryNew/trunk/G2000/Config'})
