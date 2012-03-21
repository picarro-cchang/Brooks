'''
DatEchoP3 - Listen to a path of .dat (type) files on the local system, 
and echo new rows to the P3 archive
'''
import sys
import fnmatch
import os
import time
from collections import deque
import urllib2
import urllib

import socket

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

        if 'url' in kwargs:
            self.url = kwargs['url']
        else:
            #self.url = 'http://p3.picarro.com/pge/rest/datalogAdd/'
            self.url = 'http://localhost:8080/rest/datalogAdd/'
        if 'timeout' in kwargs:
            self.timeout = int(kwargs['timeout'])
        else:
            self.timeout = 2

        if 'sleep_seconds' in kwargs:
            self.sleep_seconds = float(kwargs['sleep_seconds'])
        else:
            self.sleep_seconds = 30.0

        self._last_fname = None
        self.fname = None

    def run(self):
        '''
        '''
        ip_register_good = True
        def pushIP():
            aname = self.getLocalAnalyzerId()
            for addr in decho.getIPAddresses():
                if addr == "0.0.0.0":
                    continue
                params = {aname: {"ip_addr": "%s:5000" % addr}}
                postparms = {'data': json.dumps(params)}
                try:    
                    # NOTE: socket only required to set timeout parameter for the urlopen()
                    # In Python26 and beyond we can use the timeout parameter in the urlopen()
                    analyzerIpRegister = self.url.replace("datalogAdd", "analyzerIpRegister")
                    socket.setdefaulttimeout(self.timeout)
                    resp = urllib2.urlopen(analyzerIpRegister, data=urllib.urlencode(postparms))
                    ip_register_good = True
                    print "Registered new ip. postparms: ", postparms
                    #print "analyzerIpRegister: ", analyzerIpRegister
                    #print "resp: ", resp
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
            try:
                self.fname = genLatestFiles(*os.path.split(self.listen_path)).next()
            except:
                ecounter += 1
                time.sleep(self.sleep_seconds)
                self.fname = None
                
                if ecounter > 2000:
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
                            self.pushToP3(self.fname, None, [(line, 0)], True, None)
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
                                except:
                                    doc[col] = NaN
                            rctr += 1
                            doc['row'] = rctr
                            
                            self._lines.append((line, rctr))
                            self._docs.append(doc)
                            
                            # attempt to smooth the transmission by only
                            # sending to server every .8 seconds OR ever 100 lines
                            tsec = time.time() - nsec
                            if (lctr > 100 or tsec >= .7):
                                lctr = 0
                                self.pushToP3(self.fname, self._docs, self._lines, None, rctr)
                                self._docs = []
                                self._lines = []
                                nsec = time.time()
                                
                                if (ipctr > 100 or not ip_register_good):
                                    pushIP()
                                    ipctr = 0
                        
        
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
            params = {fname: docs}
        else:    
            params = {fname: []}
        postparms = {'data': json.dumps(params)}

        if flat_rows:
            ## flat_rows is a tuple of row, rctr
            fparams = {fname: flat_rows}
            postparms['flat_data'] = json.dumps(fparams)
        else:
            fparams = {fname: []}
            postparms['flat_data'] = json.dumps(fparams)
        
        postparms['flat_data_replace'] = 'no'
        
        if replace:
            if replace == True:
                postparms['flat_data_replace'] = 'yes'
                ##print "flat_rows in pushToP3: ", flat_rows
        
        tctr = 0
        while True:
            try:    
                # NOTE: socket only required to set timeout parameter for the urlopen()
                # In Python26 and beyond we can use the timeout parameter in the urlopen()
                socket.setdefaulttimeout(self.timeout)
                resp = urllib2.urlopen(self.url, data=urllib.urlencode(postparms))
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
            except Exception, e:
                print 'EXCEPTION in pushToP3\n%s\n' % e
                pass
            
            sys.stderr.write('-')
            tctr += 1
            time.sleep(self.timeout)
                
            ## we want to keep trying forever.  This is intentional.
            '''   
            if tctr > 100:
                print 'r\nError trying to send data from file %s to url: %s\r\n' % (self.fname, self.url)
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
            fname = genLatestFiles(*os.path.split(self.listen_path)).next()
            aname, adate, atime = analyzerNameFromFname(fname)
            return aname
        except:
            return None

if __name__ == "__main__":

    print sys.argv
    if 1 < len(sys.argv):
        listen_path=sys.argv[1]
    else:
        if hasattr(sys, "frozen"): #we're running compiled with py2exe
            AppPath = sys.executable
        else:
            AppPath = sys.argv[0]
        AppDir = os.path.split(AppPath)[0]
        listen_path = 'C:/UserData/AnalyzerServer/*_Minimal.dat'

    if 2 < len(sys.argv):
        url=sys.argv[2]
    else:
        url='http://localhost:8080/rest/datalogAdd/'
        
    if 3 < len(sys.argv):
        timeout=sys.argv[3]
    else:
        timeout=10
        
    decho = DataEchoP3(listen_path=listen_path,
                       url=url,
                       timeout=timeout)
    decho.run()
