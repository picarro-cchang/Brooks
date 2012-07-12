'''
Make a request to P3 to get some data from a log
Created on Jun 20, 2012

@author: stan
'''
import httplib
import sys
import urllib
try:
    import simplejson as json
except:
    import json

class RestCallError(Exception):
    pass
    
class RestProxy(object):
    # Proxy to make a rest call to a server
    def __init__(self,host,baseUrl):
        self.host = host
        self.baseUrl = baseUrl
    # Attributes are mapped to a function which performs
    #  a GET request to host/rest/attrName
    def __getattr__(self,attrName):
        def dispatch(argsDict):
            url = "%s/%s" % (self.baseUrl,attrName)
            print self.host, "GET","%s?%s" % (url,urllib.urlencode(argsDict))
            conn = httplib.HTTPConnection(self.host)
            try:
                conn.request("GET","%s?%s" % (url,urllib.urlencode(argsDict)))
                r = conn.getresponse()
                if not r.reason == 'OK':
                    raise RestCallError("%s: %s\n%s" % (r.status,r.reason,r.read()))
                else:
                    return json.loads(r.read()).get("result",{})
            finally:
                conn.close()
        return dispatch

def main():
    url = "p3.picarro.com/dev/rest/gdu"
    urlcomp = url.split("/",1)
    host = urlcomp[0]
    restUrl = "/"
    if len(urlcomp)>1: restUrl += urlcomp[1]
    service = RestProxy(host,restUrl)

    qryparms = {"analyzer":"FCDS2006"}
    print service.getDatLogList(qryparms)
        
if __name__ == '__main__':
    sys.exit(main())
    