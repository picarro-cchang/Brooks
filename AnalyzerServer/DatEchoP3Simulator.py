'''
DatEchoP3 - Listen to a path of .dat (type) files on the local system, 
and echo new rows to the P3 archive
'''
import sys
import os
import glob
import mmap
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


class DataEchoP3(object):
    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            self.debug = None
            
        if 'inputFile' in kwargs:
            inputFile = kwargs['inputFile']
        else:
            inputFile = None

        if 'url' in kwargs:
            self.url = kwargs['url']
        else:
            self.url = 'http://p3.picarro.com/dev/rest/datalogAdd/'

        if 'timeout' in kwargs:
            self.timeout = int(kwargs['timeout'])
        else:
            self.timeout = 2

        if 'speed_factor' in kwargs:
            self.speedFactor = float(kwargs['speed_factor'])
        else:
            self.speedFactor = 1.0

        self._last_fname = None
        self.fname = None
        
        self.analyzerName = os.path.basename(inputFile).split("-")[0]
        ip = open(inputFile,'rb')
        # memory-map the file, size 0 means whole file
        self.ipmap = mmap.mmap(ip.fileno(), 0, access=mmap.ACCESS_READ)

    def run(self):
        '''
        '''
        ip_register_good = True
        def pushIP():
            for addr in decho.getIPAddresses():
                if addr == "0.0.0.0":
                    continue
                params = {self.analyzerName: {"ip_addr": "%s:5000" % addr}}
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

        while True:
            self.fname = ('Demo_FCDS2003') + time.strftime('-%Y%m%d-%H%M%SZ-DataLog_User_Minimal.dat',time.gmtime())
            print self.fname
            pushIP()        
            self.ipmap.seek(0,0)
            headerline = self.ipmap.readline()
            headers = headerline.split()
            self.pushToP3(self.fname, None, [(headerline, 0)], True, None)
            idEpochTime = headers.index('EPOCH_TIME')
            lastEpochTime = None
            rctr = 0
            while True:
                line = self.ipmap.readline()
                if not line:
                    break
                rctr += 1
                vals = line.split()
                if not len(vals) == len(headers):
                    print '\nLEN ERROR', len(vals), len(headers)
                    print line
                    print
                    continue
                doc = dict(zip(headers, vals))
                doc['row'] = rctr

                self.pushToP3(self.fname, [doc], [(line, rctr)], None, rctr)
                
                epochTime = float(line.split()[idEpochTime])
                if not lastEpochTime:    
                    timeInterval = 0.25
                else:
                    timeInterval = epochTime - lastEpochTime
                lastEpochTime = epochTime
                
                print timeInterval
                time.sleep(timeInterval/self.speedFactor)


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
                print '\n%s\n' % e
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
        self.ipmap.seek(pos,0)
        line = self.ipmap.readline()
        while True:
            line = self.ipmap.readline()
            cpos = self.ipmap.tell()
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

if __name__ == "__main__":

    print sys.argv
    if 1 < len(sys.argv):
        inputFile=sys.argv[1]
    else:
        if hasattr(sys, "frozen"): #we're running compiled with py2exe
            AppPath = sys.executable
        else:
            AppPath = sys.argv[0]
        AppDir = os.path.split(AppPath)[0]
        inputFile = 'C:\Picarro\G2000\MobileKit\AnalyzerServer\data\Demo_FCDS2003-20111206-032437Z-DataLog_User_Minimal.dat'

    if 2 < len(sys.argv):
        speed_factor=sys.argv[2]
    else:
        speed_factor=1.0
        
    if 3 < len(sys.argv):
        url=sys.argv[3]
    else:
        url='http://p3.picarro.com/dev/rest/datalogAdd/'
        
    if 4 < len(sys.argv):
        timeout=sys.argv[4]
    else:
        timeout=10
        
    decho = DataEchoP3(inputFile=inputFile,
                       speed_factor=speed_factor,
                       url=url,
                       timeout=timeout)
    decho.run()
