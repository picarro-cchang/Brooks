# batchReportJson.py is used to run the report generation software for a collection of instruction files without
#  operator intervention. This version sends the instructions file via /rest/instrUpload2 so as to generate
#  JSON files for JavaScript report generation.

try:
    import json
except:
    import simplejson as json
import socket
import time
import urllib
import urllib2
import sys


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
        if self.sleep_seconds is None:
            self.sleep_seconds = 1.0
        self.ticket = 'None'

    def getTicket(self):
        print "Not implemented"

    def get(self, svc, ver, rsc, qryparms_obj):
        info = {}
        waitForRetryCtr = 0
        waitForRetry = True
        while True:
            rtn_data = None
            rslt = None
            err_str = None
            try:
                assert 'qry' in qryparms_obj
                qry = qryparms_obj['qry']
                del qryparms_obj['qry']
                data = urllib.urlencode(qryparms_obj)
                qry_url = '%s/rest/%s?%s' % (self.csp_url, qry, data)
                if self.debug == True:
                    print "qry_url: %s" % (qry_url)
                socket.setdefaulttimeout(self.sockettimeout)
                resp = urllib2.urlopen(qry_url, )
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
                        print 'EXCEPTION in ReportApiService - get.\n%s\n' % err_str
                    break

            except Exception, e:
                if self.debug:
                    print 'EXCEPTION in ReportApiService - get failed \n%s\n' % e

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
            waitForRetry = True

        return {"error": err_str, "return": rslt, "info": dict(info.items())}


def raiseOnError(result):
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    result = result['return']
    if 'error' in result and result['error'] is not None:
        raise RuntimeError(result['error'])
    return result


def main():
    reportApi = ReportApiService()
    reportApi.csp_url = "http://localhost:5200"
    # reportApi.ticket_url = P3Api.csp_url + "/rest/sec/dummy/1.0/Admin/"
    # reportApi.identity = "85490338d7412a6d31e99ef58bce5de6"
    # reportApi.psys = "APITEST"
    # reportApi.rprocs = '["ReportGen"]'
    reportApi.debug = False  # True

    if len(sys.argv) >= 2:
        instructions = sys.argv[1]
    else:
        instructions = raw_input("Name of instructions file? ")

    fp = open(instructions, "rb")
    contents = fp.read().splitlines()
    fp.close()

    while contents[0].startswith("//"):
        contents.pop(0)
    # Check this is valid JSON
    contents = "\n".join(contents)
    json.loads(contents)    # Throws exception on faulty JSON

    # Get the secure hash for prepending
    qryparms = {'qry': 'download', 'content': contents, 'filename': 'instructions.json'}
    contents = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

    op = file("validated.json", "wb")
    op.write(contents)
    op.close()

    qryparms = {'qry': 'validate', 'contents': contents}
    result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
    contents = result['contents']

    qryparms = {'qry': 'getTicket', 'contents': contents}
    result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
    ticket = result['ticket']

    ###
    qryparms = {'qry': 'remove', 'ticket': ticket}
    raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
    # print raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

    qryparms = {'qry': 'getReportStatus', 'ticket': ticket}
    raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

    qryparms = {'qry': 'instrUpload2', 'contents': contents}
    raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))

    status = None
    while True:
        qryparms = {'qry': 'getReportStatus', 'ticket': ticket}
        result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
        if 'files' in result and 'json' in result['files']:
            status = result['files']['json']
            if 'done' in status and status['done']:
                break
        time.sleep(2.0)

    qryparms = {'qry': 'getJson', 'ticket': ticket, 'name':'baseData', 'region':0 }
    result = raiseOnError(reportApi.get("gdu", "1.0", "ReportGen", qryparms))
    print result

if __name__ == "__main__":
    main()
