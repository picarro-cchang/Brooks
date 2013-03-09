"Routines to support Report Generation"

import calendar
import json
import hashlib
import socket
import time
import urllib
import urllib2


class Bunch:
    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)


# Status enumeration for RptGen requests
class RptGenStatus(object):
    FAILED = -4
    BAD_PARAMETERS = -2
    TASK_NOT_FOUND = -1
    NOT_STARTED = 0
    IN_PROGRESS = 1
    DONE = 16


def getMsUnixTime(timeString=None):
    if timeString is None:
        return int(1000 * time.time())
    else:
        if len(timeString) != 24 or timeString[-5] != "." or timeString[-1] != "Z":
            raise ValueError("Bad time string: %s" % timeString)
        return 1000 * calendar.timegm(time.strptime(timeString[:-5], "%Y-%m-%dT%H:%M:%S")) + int(timeString[-4:-1])


def msUnixTimeToTimeString(msUnixTime):
    u = msUnixTime // 1000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(u)) + ".%03dZ" % (msUnixTime % 1000,)


def timeStringAsDirName(ts):
    return "%013d" % getMsUnixTime(ts)


def strToEtm(s):
    "Convert string of GMT time to an Epoch Time"
    return calendar.timegm(time.strptime(s, "%Y-%m-%d  %H:%M"))


def getTicket(contents):
    "Get MD5 hash of contents"
    return hashlib.md5(contents).hexdigest()


def merge_dictionary(dst, src):
    stack = [(dst, src)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if isinstance(current_src[key], dict) and isinstance(current_dst[key], dict):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst


class ReportApiService(object):
    def __init__(self, *args, **kwargs):
        self.sockettimeout = 10
        self.csp_url = None
        if 'csp_url' in kwargs:
            self.csp_url = kwargs['csp_url']
        self.sleep_seconds = None
        if 'sleep_seconds' in kwargs:
            if kwargs['sleep_seconds']:
                self.sleep_seconds = float(kwargs['sleep_seconds'])
        if self.sleep_seconds == None:
            self.sleep_seconds = 1.0
        self.ticket = 'None'
        self.debug = False

    def getTicket(self):
        print "Not implemented"

    def get(self, svc, ver, rsc, qryparms_obj):
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            rtn_data = None
            rslt = None
            err_str = None
            try:
                data = urllib.urlencode(qryparms_obj)
                qry_url = '%s/rest/%s?%s' % (self.csp_url, rsc, data)
                if self.debug == True:
                    print "qry_url: %s" % (qry_url)
                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_url)
                info = resp.info()
                rtn_data = resp.read()

            except urllib2.HTTPError, e:
                err_str = e.read()
                if "invalid ticket" in err_str:
                    if self.debug == True:
                        print "We Have an invalid or expired ticket"
                    self.getTicket()
                    waitForRetryCtr += 1
                    if waitForRetryCtr < 100:
                        waitForRetry = None
                else:
                    if self.debug == True:
                        print 'EXCEPTION in ReportApiService - get.\n%s\n' \
                            % err_str
                    info = {}
                    break

            except Exception, e:
                if self.debug:
                    print 'EXCEPTION in ReportApiService - get failed \n%s\n' \
                        % e

                time.sleep(self.sleep_seconds)
                continue

            if (rtn_data):
                if 'json' in info['content-type']:
                    rslt = json.loads(rtn_data)
                    if self.debug == True:
                        print "rslt: ", rslt
                else:
                    print "rslt of type: ", info['content-type']
                    rslt = rtn_data
                break

            if waitForRetry:
                time.sleep(self.timeout)
                print "Looping"
            waitForRetry = True

        return {"error": err_str, "return": rslt, "info": dict(info.items())}
