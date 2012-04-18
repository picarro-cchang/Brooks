'''
DatEchoP3 - Listen to a path of .dat (type) files on the local system, 
and echo new rows to the P3 archive
'''
import sys
from optparse import OptionParser

import fnmatch
import os
import time
from collections import deque
import urllib2
import urllib
import math

import socket
import datetime

try:
    import simplejson as json
except:
    import json

from ctypes import Structure, windll, sizeof
from ctypes import POINTER, byref
from ctypes import c_ulong, c_uint, c_ubyte, c_char

NaN = 1e1000/1e1000

def genLatestFiles(baseDir,pattern):
    # Generate files in baseDir and its subdirectories which match pattern
    for dirPath, dirNames, fileNames in os.walk(baseDir):
        dirNames.sort(reverse=True)
        fileNames.sort(reverse=True)
        for name in fileNames:
            if fnmatch.fnmatch(name,pattern):
                yield os.path.join(dirPath,name)

class DataEchoP3(object):
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
        if 'listen_path' in kwargs:
            self.listen_path = kwargs['listen_path']
        else:
            self.listen_path = None

        if 'file_path' in kwargs:
            self.file_path = kwargs['file_path']
        else:
            self.file_path = None

        if not self.listen_path:
            if not self.file_path:
                self.listen_path = 'C:/UserData/AnalyzerServer/*_Minimal.dat'

        if 'ip_url' in kwargs:
            self.ip_url = kwargs['ip_url']
        else:
            #self.ip_url = 'https://dev.picarro.com/node/gdu/abcdefg/1/AnzMeta/'
            self.ip_url = None

        if 'push_url' in kwargs:
            self.push_url = kwargs['push_url']
        else:
            #self.push_url = 'http://localhost:8080/rest/datalogAdd/'
            self.push_url = 'https://dev.picarro.com/node/gdu/abcdefg/1/AnzLog/'
            
        if 'ticket_url' in kwargs:
            self.ticket_url = kwargs['ticket_url']
        else:
            self.ticket_url = 'https://dev.picarro.com/node/gdu/abcdefg/1/AnzLog/'
            
        if 'timeout' in kwargs:
            self.timeout = int(kwargs['timeout'])
        else:
            self.timeout = 2

        if 'replace' in kwargs:
            self.replace = kwargs['replace']
        else:
            self.replace = None

        if 'logtype' in kwargs:
            self.logtype = kwargs['logtype']
        else:
            self.logtype = "dat"

        if 'identity' in kwargs:
            self.identity = kwargs['identity']
        else:
            self.identity = None

        if 'psys' in kwargs:
            self.psys = kwargs['psys']
        else:
            self.psys = None

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0

        self._last_fname = None
        self.fname = None
        self.first_pass_complete = None
        self.ticket = None
        self.startTime = datetime.datetime.now()

    def getTicket(self):
        self.ticket = None
        ticket = None
        qry = "issueTicket"
        sys = self.psys
        identity = self.identity
        rprocs = '["AnzMeta:data", "AnzLog:data"]'
        
        params = {"qry": qry, "sys": sys, "identity": identity, "rprocs": rprocs}
        try:
            resp = urllib2.urlopen(self.ticket_url, data=urllib.urlencode(params))
            rtndata_str = resp.read()
            rtndata = json.loads(rtndata_str)
            if "ticket" in rtndata:
                ticket = rtndata["ticket"]

        except urllib2.HTTPError, e:
            err_str = e.read()
            print '\nissueTicket failed \n%s\n' % err_str
                
        except Exception, e:
            print '\nissueTicket failed \n%s\n' % e

        if ticket:
            self.ticket = ticket;
            print "new ticket: ", self.ticket
        

    def run(self):
        '''
        '''
        
        if not self.identity:
            print "Cannot proceed. No Identity for authentication"
            sys.exit()
            
        if not self.ticket:
            self.ticket = "abcdefg"
            
        ip_register_good = True
        def pushIP():
            aname = self.getLocalAnalyzerId()
            if self.psys == None:
                self.psys = aname
                
            if self.ip_url:
                for addr in self.getIPAddresses():
                    if addr == "0.0.0.0":
                        continue
                    
                    
                    doc_data = []
                    datarow = {}
                    datarow["ANALYZER"] = aname
                    datarow["PRIVATE_IP"] = "%s:5000" % addr 
                    doc_data.append(datarow)
                    postparms = {'data': json.dumps(doc_data)}
                    
                    continueRequest = True;
                    continueRequestCtr = 0;
                    while continueRequest:
                        continueRequest = None
                        
                        try:    
                            # NOTE: socket only required to set timeout parameter for the urlopen()
                            # In Python26 and beyond we can use the timeout parameter in the urlopen()
                            analyzerIpRegister = self.ip_url.replace("<TICKET>", self.ticket)
                            print "analyzerIpRegister: ", analyzerIpRegister
                            socket.setdefaulttimeout(self.timeout)
                            resp = urllib2.urlopen(analyzerIpRegister, data=urllib.urlencode(postparms))
                            ip_register_good = True
                            print "Registered new ip. postparms: ", postparms
                            break
                        
                        except urllib2.HTTPError, e:
                            err_str = e.read()
                            if "invalid ticket" in err_str:
                                if continueRequestCtr < 10:
                                    print "We Have an invalid or expired ticket"
                                    continueRequest = True
                                    continueRequestCtr += 1
                                    self.getTicket()
                                
                            else:
                                ip_register_good = False
                                print '\nanalyzerIpRegister failed \n%s\n' % err_str
                                
                            break
                            
                        except Exception, e:
                            ip_register_good = False
                            print '\nanalyzerIpRegister failed \n%s\n' % e
                            pass

        ecounter = 0
        fcounter = 0
        wcounter = 0
        while True:
            # Getting source
            if self.file_path:
                if self.fname == os.path.join(self.file_path):
                    print "processing complete for file_path: %s" % self.fname
                    break
                else:
                    self.fname = os.path.join(self.file_path)
                    
            else:
                try:
                    self.fname = genLatestFiles(*os.path.split(self.listen_path)).next()
                except:
                    ecounter += 1
                    time.sleep(self.sleep_seconds)
                    self.fname = None
                    
                    if ecounter > 200000:
                        print "listen_path: %s" % self.listen_path
                        print "No files to process: Exiting DataEchoP3.run()"
                        break
                    else:
                        print "No files to process: sleeping for %s seconds" % self.sleep_seconds

            # if we have a file, make sure we have not previously processed it
            ##  if we have proccessed it, sleep for a wile, and wait for a new file
            ##  if we have slept too many times, exit.            
            pushIP()        
            if self.fname:
                if self.fname == self._last_fname: 
                    wcounter += 1
                    time.sleep(1.0)
                    
                    if wcounter > 10: 
                        print "No more files to process: Exiting DataEchoP3.run()"
                        break
                else:
                    self._last_fname = self.fname
                    first_row = True
                    headers = None
                    rctr = 0
                    lctr = 0
                    ipctr = 0
                    nsec = time.time()
                    self._docs = []
                    self._lines = []
                    for line in self.iterate_file():
                        if first_row:
                            first_row = None
                            headers = line.split()
                            ##print "line", line
                            
                            ## We no longer push the file line
                            #self.pushToP3(self.fname, None, [(line, 0)], True, None)
                            continue
                        
                        lctr += 1
                        ipctr += 1
                        if headers:
                            vals = line.split()
                            if not len(vals) == len(headers):
                                print '\nLEN ERROR', len(vals), len(headers)
                                print line
                                print
                                continue
                            
                            doc = {}
                            for col, val in zip(headers, vals):
                                try:
                                    doc[col] = float(val)
                                    #JSON does not have NaN as part of the standard
                                    # (even though JavaScrip does)
                                    # so send a text "NaN" and the server will convert
                                    if math.isnan(doc[col]):
                                        doc[col] = "NaN"
                                except:
                                    #JSON does not have NaN as part of the standard
                                    # (even though JavaScrip does)
                                    # so send a text "NaN" and the server will convert
                                    doc[col] = "NaN"

                            rctr += 1
                            doc['row'] = rctr
                            
                            self._lines.append((line, rctr))
                            self._docs.append(doc)
                            
                            # attempt to smooth the transmission by only
                            # sending to server every .8 seconds OR ever 100 lines
                            tsec = time.time() - nsec
                            if (lctr > 2000 or tsec >= .7):
                                lctr = 0
                                self.pushToP3(self.fname, self._docs, self._lines, None, rctr)
                                self._docs = []
                                self._lines = []
                                nsec = time.time()
                                
                                if (ipctr > 5000 or not ip_register_good):
                                    pushIP()
                                    ipctr = 0
                        
        
        self.endTime = datetime.datetime.now()
        print "start: ", self.startTime
        print "end: ", self.endTime
        
        return fcounter

    def iterate_file(self):
        '''
        a generator which yields rows (lines) from the
        '''
        fp = file(self.fname,'rb')
        print "\r\nOpening source stream %s\r\n" % self.fname
        counter = 0
        while True:
            line = fp.readline()
            sys.stderr.write('.')
            if not line:

                # clear the remaining data
                if self._docs or self._lines:
                    self.pushToP3(self.fname, self._docs, self._lines, None, None)
                    self._docs = []
                    self._lines = []
                
                counter += 1
                if counter == 10:
                    try:    # Stop iteration if we are not the last file
                        if self.fname == os.path.join(self.file_path):
                            fp.close()
                            print "\r\nClosing source stream %s\r\n" % self.fname
                            return
                        
                        if self.fname != genLatestFiles(*os.path.split(self.listen_path)).next(): 
                            fp.close()
                            print "\r\nClosing source stream %s\r\n" % self.fname
                            return
                    except:
                        pass
                    counter = 0
                time.sleep(0.1)
                continue
            
            yield line

    def pushToP3(self, path, docs=None, flat_rows=None, replace=None, last_pos=None):
        err_rtn_str = 'ERROR: missing data:'
        rtn = "OK"
        fname = os.path.basename(path) 
        if docs: 
            replace_the_log = None
            if (not self.first_pass_complete):
                if (self.replace == True):
                    replace_the_log = 1
                    
            params = [{"logname": fname, "replace": replace_the_log, "logtype": self.logtype, "logdata": docs}]
            postparms = {'data': json.dumps(params)}
        
            tctr = 0
            waitForRetryCtr = 0
            waitForRetry = True
            while True:
                
                try:    
                    # NOTE: socket only required to set timeout parameter for the urlopen()
                    # In Python26 and beyond we can use the timeout parameter in the urlopen()
                    socket.setdefaulttimeout(self.timeout)
                    myDat = urllib.urlencode(postparms)
                    push_with_ticket = self.push_url.replace("<TICKET>", self.ticket)
                    resp = urllib2.urlopen(push_with_ticket, data=myDat)
                    rtn_data = resp.read()
                    ##print rtn_data
                    if err_rtn_str in rtn_data:
                        rslt = json.loads(rtn_data)
                        expect_ctr = rslt['result'].replace(err_rtn_str, "").strip()
                        if last_pos:
                            missing_rtn = self.pushMissingRows(path, int(expect_ctr), last_pos)
                        else:
                            break
                    else:
                        break
                    
                except urllib2.HTTPError, e:
                    err_str = e.read()
                    if "invalid ticket" in err_str:
                        print "We Have an invalid or expired ticket"
                        self.getTicket()
                        waitForRetryCtr += 1
                        if waitForRetryCtr < 100:
                            waitForRetry = None
                        
                    else:
                        print 'Ticket EXCEPTION in pushToP3, and could not get valid ticket.\n%s\n' % err_str
                        pass
                    
                except Exception, e:
                    print 'EXCEPTION in pushToP3\n%s\n' % e
                    pass
                    
                sys.stderr.write('-')
                tctr += 1
                if waitForRetry:
                    time.sleep(self.timeout)
                    
                waitForRetry = True
                
            ## we want to keep trying forever.  This is intentional.
            '''   
            if tctr > 100:
                print 'r\nError trying to send data from file %s to url: %s\r\n' % (self.fname, self.push_url)
                rtn = "ERROR"
                break
            '''
            
        return rtn
    
    def pushMissingRows(self, path, pos, last_pos):
        fp = file(self.fname,'rb')
        fp.seek(pos,0)
        line = fp.readline()
        while True:
            line = fp.readline()
            cpos = fp.tell()
            sys.stderr.write('+')
            if line:
                print "trying for missing!"
                self.pushToP3(self.fname, None, [(line, cpos)], None, None)
            else:
                return "ERROR"
            if cpos >= last_pos:
                break
            
        return "OK"
            
        
        
    def getIPAddresses(self):
        MAX_ADAPTER_DESCRIPTION_LENGTH = 128
        MAX_ADAPTER_NAME_LENGTH = 256
        MAX_ADAPTER_ADDRESS_LENGTH = 8
        class IP_ADDR_STRING(Structure):
            pass
        LP_IP_ADDR_STRING = POINTER(IP_ADDR_STRING)
        IP_ADDR_STRING._fields_ = [
            ("next", LP_IP_ADDR_STRING),
            ("ipAddress", c_char * 16),
            ("ipMask", c_char * 16),
            ("context", c_ulong)]
        class IP_ADAPTER_INFO (Structure):
            pass
        LP_IP_ADAPTER_INFO = POINTER(IP_ADAPTER_INFO)
        IP_ADAPTER_INFO._fields_ = [
            ("next", LP_IP_ADAPTER_INFO),
            ("comboIndex", c_ulong),
            ("adapterName", c_char * (MAX_ADAPTER_NAME_LENGTH + 4)),
            ("description", c_char * (MAX_ADAPTER_DESCRIPTION_LENGTH + 4)),
            ("addressLength", c_uint),
            ("address", c_ubyte * MAX_ADAPTER_ADDRESS_LENGTH),
            ("index", c_ulong),
            ("type", c_uint),
            ("dhcpEnabled", c_uint),
            ("currentIpAddress", LP_IP_ADDR_STRING),
            ("ipAddressList", IP_ADDR_STRING),
            ("gatewayList", IP_ADDR_STRING),
            ("dhcpServer", IP_ADDR_STRING),
            ("haveWins", c_uint),
            ("primaryWinsServer", IP_ADDR_STRING),
            ("secondaryWinsServer", IP_ADDR_STRING),
            ("leaseObtained", c_ulong),
            ("leaseExpires", c_ulong)]
        GetAdaptersInfo = windll.iphlpapi.GetAdaptersInfo
        GetAdaptersInfo.restype = c_ulong
        GetAdaptersInfo.argtypes = [LP_IP_ADAPTER_INFO, POINTER(c_ulong)]
        adapterList = (IP_ADAPTER_INFO * 10)()
        buflen = c_ulong(sizeof(adapterList))
        rc = GetAdaptersInfo(byref(adapterList[0]), byref(buflen))
        if rc == 0:
            for a in adapterList:
                adNode = a.ipAddressList
                while True:
                    ipAddr = adNode.ipAddress
                    if ipAddr:
                        yield ipAddr
                    adNode = adNode.next
                    if not adNode:
                        break
        
    def getLocalAnalyzerId(self):
        def analyzerNameFromFname(fname):
            '''
            analyzer path from the analyzer file name
            name is in form of XXXXXXXX-YYYYMMDD-HHMMSSZ-blah-blah-blah
            '''
            fbase = os.path.basename(fname)
            aname, sep, part = fbase.partition('-')
            adate, sep, part = part.partition('-')
            atime, sep, part = part.partition('-')
            return aname, adate, atime

                    
            
        try:    # Stop iteration if we are not the last file
            if self.file_path:
                fname = os.path.join(self.file_path)
            else:
                fname = genLatestFiles(*os.path.split(self.listen_path)).next()
                
            aname, adate, atime = analyzerNameFromFname(fname)
            return aname
        except:
            return None

def main(argv=None):
    if argv is None:
        argv = sys.argv
        
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--data-type", dest="data_type",
                      help="Data type (log type).", metavar="<DATA_TYPE>")
    parser.add_option("-l", "--listen-path", dest="listen_path",
                      help="Search path for constant updates.", metavar="<LISTEN_PATH>")
    parser.add_option("-f", "--file-path", dest="file_path",
                      help="path to specific file to upload.", metavar="<FILE_PATH>")
    parser.add_option("-t", "--timeout", dest="timeout",
                      help="timeout value for response from server.", metavar="<TIMEOUT>")
    parser.add_option("-i", "--ip-req-url", dest="ip_url",
                      help="rest url for ip registration. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<IP_REQ_URL>")
    parser.add_option("-p", "--push-url", dest="push_url",
                      help="rest url for data push to server. Use the string <TICKET> as the place-holder for the authentication ticket.", metavar="<PUSH_URL>")
    parser.add_option("-k", "--ticket-url", dest="ticket_url",
                      help="rest url for authentication ticket.", metavar="<TICKET_URL>")
    parser.add_option("-y", "--identity", dest="identity",
                      help="Authentication identity string.", metavar="<IDENTITY>")
    parser.add_option("-s", "--sys", dest="psys",
                      help="Authentication sys.", metavar="<SYS>")
    parser.add_option("-r", "--replace", dest="replace", action="store_true",
                      help="replace this log in the server (Dangerous!!, use with caution. This will delete FIRST!).")
    
    (options, args) = parser.parse_args()
    #if len(args) != 1:
    #    parser.error("incorrect number of arguments")
        
    if options.listen_path and options.file_path:
        parser.error("listen-path and file-path are mutually exclusive")
        
    if options.listen_path and options.replace:
        parser.error("listen-path and replace are mutually exclusive")
        
    if options.listen_path:
        listen_path = options.listen_path
    else:
        listen_path = None
        
    if options.file_path:
        file_path = options.file_path
    else:
        file_path = None

    if not listen_path:
        if not file_path:
            listen_path = 'C:/UserData/AnalyzerServer/*_Minimal.dat'
            
    if options.timeout:
        timeout = options.timeout
    else:
        timeout = 10

    if options.ip_url:
        ip_url = options.ip_url
    else:
        ip_url = None
        
    if options.push_url:
        push_url = options.push_url
    else:
        push_url = 'https://dev.picarro.com/node/gdu/<TICKET>/1/AnzLog/'

    if options.ticket_url:
        ticket_url = options.ticket_url
    else:
        ticket_url = 'https://dev.picarro.com/node/gdu/dummy/1/Admin/'

    if options.psys:
        psys = options.psys
    else:
        psys = None

    if options.identity:
        identity = options.identity
    else:
        identity = None

    if options.data_type:
        logtype = options.data_type
    else:
        logtype = "dat"

    if options.replace:
        replace = options.replace
    else:
        replace = None

    print "listen_path", listen_path
    print "file_path", file_path
    print "ip_url", ip_url
    print "push_url", push_url
    print "ticket_url", ticket_url
    print "identity", identity
    print "psys", psys
    print "timeout", timeout
    print "logtype", logtype

    decho = DataEchoP3(listen_path=listen_path,
                       file_path=file_path,
                       ip_url=ip_url,
                       push_url=push_url,
                       ticket_url=ticket_url,
                       psys=psys,
                       identity=identity,
                       timeout=timeout,
                       logtype=logtype,
                       replace=replace)
    decho.run()

if __name__ == '__main__':
    sys.exit(main())

