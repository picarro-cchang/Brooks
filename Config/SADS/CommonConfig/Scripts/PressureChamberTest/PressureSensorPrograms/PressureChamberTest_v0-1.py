# -*- coding: utf-8 -*-
"""
Created on Tue Oct 01 14:49:03 2013

@author: chris
20140326 - added Alicat Pressure sensor (rella)
"""

import msvcrt 
import time
import RS232_VALCO_ALICAT_20140326 as VA
import string
try:
    import CmdFIFO
    fifoflag = True
except:
    print "can't communicate with instrument"
    fifoflag = False

def genCOMstep(vstring,trans):
    for e in trans:
        vstring = vstring.replace(e,trans[e])
    return vstring

ENABLE_COMMANDS = False
TIMESTEP = 1.0

LOAD = r'I:GOA:2,S:GO1:z,S:GO2:z,S:GO3:z,S:GO4:z,S:GO5:z,S:GO6:z,S:GOw:2'
LTIME = '20'

LOAD1 = {'z':LTIME,'w':'1'}

L1 = genCOMstep(LOAD,LOAD1)

MTIME = '300'

MEAS =  r'S:GOf:2,I:GOB:y,S:GOa:y,S:GOb:y,S:GOc:y,S:GOd:y,S:GOe:y,S:GOf:z'
MEASF = {'a':'2','b':'3','c':'4','d':'5','e':'6','f':'1','y':MTIME,'z':'120'}
MEASR = {'a':'5','b':'4','c':'3','d':'2','e':'1','f':'6','y':MTIME,'z':'120'}

MF = genCOMstep(MEAS,MEASF)
MR = genCOMstep(MEAS,MEASR)
print MR

COMLIST = []

def kbfunc(): 
   ret = r''
   while msvcrt.kbhit():
       ret += msvcrt.getch()
       time.sleep(0.001)
   return ret

def parseCom(comstring):        #colon delimited string D=device:s=commandstring:t = delay to next command
    return string.split(comstring,':')

def parseComList(seqstring):
    return string.split(seqstring,',')
    

if __name__ == "__main__":

    if fifoflag == True:
        MeasSystem = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % 50070,
                                    'AuxStuff', IsDontCareConnection = False)
    else:
        f_log = open('f_log_%d.txt' % time.time(), 'w')
    P = VA.device(dtype = 'Alicat P', name = 'Alicat P-30PSIA', query = 'A', response = 'A +', nickname = 'Amb')
#    F = VA.device(dtype = 'Alicat Meter', name = 'Alicat 500sccm', query = 'A', response = 'A +', nickname = 'FM')
#    M = VA.device(dtype = 'Alicat MFC', name = 'Alicat 500sccm', query = 'M', response = 'M +', nickname = 'FM')
#    D = VA.device(dtype = 'Alicat MFC', name = 'Alicat 2slm', query = 'D', response = 'D +', nickname = 'FD')
#    I = VA.device(dtype = 'Valco 2P', name = '6-port 2-position Valve', query = 'VR', response = 'I-PD-EHF56RD.4', nickname = 'VI')
#    S = VA.device(dtype = 'Valco MPV', name = '6-port Selector Valve', query = 'VR', response = 'I-PD-AMTX88RD1', nickname = 'VS')  #UC valco selector
    #S = VA.device(dtype = 'Valco MPV', name = '6-port Selector Valve', query = 'VR', response = 'I-PD-AMHX88RD1', nickname = 'VS')  #Picarro selector
    
    qflag = False   
    nextcom = True
    nextmark = time.time()
    while not(qflag):
        dt = time.time() - nextmark
        print "%.1f\r" % dt,
        if dt > 0.0 and ENABLE_COMMANDS:
            try:
                c = COMLIST.pop(0)
                a = parseCom(c)
                print '%s   %s   wait %s sec' % (a[0],a[1],a[2])
                if a[0] == 'D': #dilution MFC
                    print D.sendCommand(a[1], readback = False)
                elif a[0] == 'M': #membrane MFC
                    print M.sendCommand(a[1],readback = False)
                elif a[0] == 'I': #inject / load Valco
                    print I.sendCommand(a[1],readback = False)
                elif a[0] == 'S': #selector Valco
                    print S.sendCommand(a[1],readback = False)
                else:
                    pass
                nextmark = time.time() + float(a[2])
            except:
                pass
            
        res1 = P.sendAndParse('A')          # read MFC and valve states
        #res2 = D.sendAndParse('D')
        #res3 = I.sendAndParse('CP')
        #res4 = S.sendAndParse('CP')
        results = dict(res1.items())
        if fifoflag == True:
            for things in results:              # stuff data into instrument data file via RPCbackdoor
                try:
                    MeasSystem.Backdoor.SetData(things,results[things])
                except:
                    pass
        else:
            
            rlist = ['%.3f' % results[a] for a in results]
            savetxt = '%d,' % time.time()
            savetxt += ','.join(rlist) + '\n'
            f_log.write(savetxt)
            f_log.flush()
            
        #### check for keyboard commands -- add commands to list
        kb = kbfunc()
        if kb != '' and ENABLE_COMMANDS:
            print '* %s *' % kb
        
            if kb == 'L' or kb == 'l':
                print 'loading sample loops, ending on 1'
                COMLIST = parseComList(L1)
                nextmark = time.time()
            elif kb == 'F' or kb == 'f':
                print 'cycling selector valve from 1 to 6'
                COMLIST = parseComList(MF)
                nextmark = time.time()
            elif kb == 'R' or kb == 'r':
                print 'cycling selector valve from 6 to 1'
                COMLIST = parseComList(MR)
                nextmark = time.time()
            elif kb == '1':
                print 'loading, then measuring from 1 to 6'
                COMLIST = parseComList(L1)
                COMLIST += parseComList(MF)
                nextmark = time.time()
            elif kb == '6':
                print 'loading, then measuring from 6 to 1'
                COMLIST = parseComList(L1)
                COMLIST += parseComList(MR)
                print len(COMLIST)
                nextmark = time.time()
            elif kb == 'n':
                nextmark = time.time()
            elif kb == 'q':
                print 'clearing command buffer'
                COMLIST = []
                nextmark = time.time()
            else:
                print 'command not recognized'
                
        dt = time.time() - nextmark
        if dt > -2*TIMESTEP and dt < 0.0:          #wait until it is time until the next command
            wait = nextmark - time.time() + 0.05
            if wait > 2*TIMESTEP:
                wait = 2*TIMESTEP
            if wait < 0.001:
                wait = 0.001
        else:
            wait = TIMESTEP
        time.sleep(wait)
        
        
        
