"""
Copyright 2013 Picarro Inc.
"""

import urllib2
import time

import simplejson as json


class TestReferenceGas(object):

    def setup_method(self, m):
        self.urlRoot = 'http://localhost:5000/rest'

    def testPulseGeneration(self):
        print 'Requires that the reference gas inlet be attached to the ' \
            '20 ppm methane bottle.'

        r = urllib2.urlopen("%s/setCurrentReference?reference=ISOTOPIC" %
                            self.urlRoot)
        result = json.loads(r.read())
        assert result['result'] == 'OK'

        r = urllib2.urlopen("%s/getCurrentReference" % self.urlRoot)
        result = json.loads(r.read())
        assert result['result'] == 'ISOTOPIC'

        r = urllib2.urlopen("%s/restartDatalog" % self.urlRoot)
        r.read()

        for i in range(10):
            time.sleep(30.0)

            r = urllib2.urlopen("%s/setCurrentReference?reference=ISOTOPIC" %
                                self.urlRoot)
            result = json.loads(r.read())
            assert result['result'] == 'OK'

            time.sleep(600.0)

            r = urllib2.urlopen(
                "%s/setCurrentReference?reference=CONCENTRATION" % self.urlRoot)
            result = json.loads(r.read())
            assert result['result'] == 'OK'

        r = urllib2.urlopen("%s/restartDatalog" % self.urlRoot)
        r.read()
