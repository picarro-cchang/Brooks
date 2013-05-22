"""
Copyright 2013 Picarro Inc.
"""

import urllib2
import time

import simplejson as json


class TestBumperMast(object):

    def setup_method(self, m):
        self.urlRoot = 'http://localhost:5000/rest'

    def testPulseGeneration(self):
        print 'Requires that the "Bumper" be attached to the 20 ppm methane ' \
            'bottle.'

        r = urllib2.urlopen("%s/setCurrentInlet?inlet=MAST" % self.urlRoot)
        result = json.loads(r.read())
        assert result['result'] == 'OK'

        r = urllib2.urlopen("%s/getCurrentInlet" % self.urlRoot)
        result = json.loads(r.read())
        assert result['result'] == 'Mast'

        r = urllib2.urlopen("%s/restartDatalog" % self.urlRoot)
        r.read()

        for i in range(10):
            time.sleep(5.0)

            r = urllib2.urlopen("%s/setCurrentInlet?inlet=MAST" % self.urlRoot)
            result = json.loads(r.read())
            assert result['result'] == 'OK'

            time.sleep(5.0)

            r = urllib2.urlopen("%s/setCurrentInlet?inlet=BUMPER" % self.urlRoot)
            result = json.loads(r.read())
            assert result['result'] == 'OK'

        r = urllib2.urlopen("%s/restartDatalog" % self.urlRoot)
        r.read()
