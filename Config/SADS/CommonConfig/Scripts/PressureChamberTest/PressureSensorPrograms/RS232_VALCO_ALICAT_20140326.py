# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 10:49:43 2013

@author: chris

20140326 - added Alicat Pressure sensor to the list of accepted devices
"""

import serial
import time
import string
try:
    import CmdFIFO
except:
    pass

class device:
    # parameters in D: baud, timeout, data bits, stop bits, parity, line terminator, overall timeout
    D = {'Alicat Meter':[19200,0.1,8,1,'N','\r',0.5],
         'Valco MPV':[9600,0.1,8,1,'N','\r',3],
         'Valco 2P':[9600,0.1,8,1,'N','\r',3],
         'Alicat MFC':[19200,0.1,8,1,'N','\r',0.5],
         'Alicat P':[19200,0.1,8,1,'N','\r',0.5]}
    def __init__(self,port = None, name = 'device0', dtype = None, 
                 query = "*IDN", response = None, nickname = 'a'):
        self.name = name
        self.nickname = nickname
        self.dtype = dtype         
        self.baud = self.D[dtype][0]
        self.timeout = self.D[dtype][1]
        self.databits = self.D[dtype][2]
        self.stopbits = self.D[dtype][3]
        self.parity = self.D[dtype][4]
        self.term = self.D[dtype][5]
        self.finaltimeout = self.D[dtype][6]
        self.query = query
        self.response = response
        
        if port is None:
            for n,s in self.scan():
                k = self.findDevice(n,s)
                if k is not(None):
                    self.port = k
                    print "%s found on port %s" % (self.name, self.port)
                    break
            else:
                self.port = None
                print "%s not found" % self.name
        else:
            self.port = port
        self.serialDevice = self.openDevice(self.port)
        
    def sendAndParse(self,comstring, readback = True):
        res = self.sendCommand(comstring, readback = True)
        return self.parseResponse(res)

    def sendCommand(self,comstring, readback = True):
        if self.port != None:
            self.serialDevice.write("%s%s" % (comstring,self.term))
            t0 = time.time()
            x = ''
            if readback is True:
                while (len(x) == 0) and ((time.time() - t0) < self.finaltimeout):
                    x += self.serialDevice.read(50)
            if len(x) == 0:
                x = 'no readback!'
        else:
            x = 'device not present'
        return x   
    
    def parseResponse(self,x):
        if self.port != None:
            pre = self.nickname
            if self.dtype == 'Alicat Meter':
                y = string.split(x,' ')
                z = [c for c in y if c != '']
                data = {'%s_P_amb' % pre:float(z[1]), '%s_T_amb' % pre:float(z[2]), '%s_flow' % pre:float(z[4])}
            elif self.dtype == 'Alicat MFC':
                y = string.split(x,' ')
                z = [c for c in y if c != '']
                data = {'%s_P_amb' % pre:float(z[1]), '%s_T_amb' % pre:float(z[2]), '%s_flow' % pre:float(z[4]), '%s_flowset' % pre:float(z[5])}
            elif self.dtype == 'Alicat P':
                y = string.split(x,' ')
                z = [c for c in y if c != '']
                data = {'%s_P' % pre:float(z[1])}
            elif self.dtype == 'Valco MPV':
                if x.find('Position is  =') != -1:
                    data = {'%s_CP' % pre:int(x[-2:])}
                else:
                    data = {}
            elif self.dtype == 'Valco 2P':
                if x.find('Position is') != -1:
                    p = x[-3]
                    if p == 'A':
                        pn = 0
                    elif p == 'B':
                        pn = 1
                    else:
                        pn = -1
                    data = {'%s_CP' % pre:pn}
                else:
                    data = {'%s_CP' % pre:-1}
            else:
                data = {}
            print x
            if data == {}:
                print ' -- no data received'
        else:
            data = {}
        return data
    
    def openDevice(self,portn):
        return serial.Serial(portn,baudrate = self.baud,timeout = self.timeout,
                                 bytesize = self.databits, stopbits = self.stopbits,
                                 parity = self.parity)             
            
    def scan(self):
        # scan for available ports. return a list of tuples (num, name)
        available = []
        print 'Scanning COM ports for %s ...' % self.name
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append( (i, s.portstr))
                s.close()
            except serial.SerialException:
                pass
        return available
        
    def findDevice(self,n,s):
        try:
            port = self.openDevice(n)
            print s
            port.write("%s%s" % (self.query,self.term))
            x = port.read(50)
            x = x.replace('\r','\r\n')
            print x
            if x.find(self.response) != -1:
                return n
            else:
                return None
            port.close()
        except:
            pass
        
    def __str__(self):
        t = "*****   %s  *****\n" % self.name
        t += "  port = %s\n" % self.port
        t += "  baud = %s \n  timeout = %s\n" % (self.baud,self.timeout)
        t += "  data bits = %s\n  stop bits = %s\n  parity = %s" % (self.databits, self.stopbits, self.parity)
        return t

    # MEAS_SYSTEM is on port 50070

if __name__ == '__main__':
#    MeasSystem = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % 50070,
#                                    'AuxStuff', IsDontCareConnection = False)
    MFC_Membrane = device(dtype = 'Alicat MFC', name = 'Alicat 500sccm', query = 'M', response = 'M +', nickname = 'FM')
    MFC_Dilution = device(dtype = 'Alicat MFC', name = 'Alicat 2slm', query = 'D', response = 'D +', nickname = 'FD')
    Inject = device(dtype = 'Valco 2P', name = '6-port 2-position Valve', query = 'VR', response = 'I-PD-EHF56RD.4', nickname = 'VI')
    Loop = device(dtype = 'Valco MPV', name = '6-port Selector Valve', query = 'VR', response = 'I-PD-AMTX88RD1', nickname = 'VS')
    while True:
        time.sleep(2)
        res1 = MFC_Membrane.parseResponse(MFC_Membrane.sendCommand('M'))
        res2 = MFC_Dilution.parseResponse(MFC_Dilution.sendCommand('D'))
        res3 = Inject.parseResponse(Inject.sendCommand('CP'))
        res4 = Loop.parseResponse(Loop.sendCommand('CP'))
        results = dict(res1.items() + res2.items() + res3.items() + res4.items())
        for things in results:
            pass
#            MeasSystem.Backdoor.SetData(things,results[things])
    else:
        MFC_Membrane.serialDevice.close()
        MFC_Dilution.serialDevice.close()
        Inject.serialDevice.close()
        Loop.serialDevice.close()

    """Control command list
VR  - firmware version
NPn - number of pos.
GOn - shortest move to n
CWn - clockwise move to n
CCn - cntr_clockwise move to n
IDn - "0" - "9"
CP  - current pos.
SBn-n - baud rate (i.e. 9600)
SDn - dig. in mode "0" - "3"
      0=BCD 1=Disa. 2=Para. 3=Bin.
SOn - pos. offset "1" - ("98" - NP)
SLn - latch disable "1"
SMc - rotation dir
      F=for. R=rev. or A=auto
 ?  - list"""