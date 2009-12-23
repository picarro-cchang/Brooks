#!/usr/bin/env python
#
# File Name: TestUtilities.py
# Purpose: Utility routines for generating reports from CRDStest software
#
# Notes:
#
# File History:
# 06-01-13 sze   Initial version
# 06-02-30 sze   Moved code for reading Burleigh and Ophir to here

from numpy import *
from pylab import *
from TestDescriptions import *
import time
import types
import os
from threading import Thread
import serial

class KeithleyReply(object):
    def __init__(self,ser,interchar_timeout):
        self.ser = ser
        self.interchar_timeout = interchar_timeout
        self.string = ""
        self.tlast = None

    def fetch(self):
        while True:
            ch = self.ser.read()
            if ch == "": break
            if ch == "\r": continue
            self.string = self.string + ch
            self.tlast = time.clock()
            if ch == "\n":
                result = self.string
                self.string = ""
                self.tlast = None
                return result
        if self.tlast!=None and time.clock()-self.tlast > self.interchar_timeout:
            result = self.string
            self.string = ""
            self.tlast = None
            return result
        return ""

    def getString(self):
        while True:
            s = self.fetch()
            if s != "": return s

    def sendString(self,string):
        self.ser.write(string + "\r")

    def ask(self,string):
        self.sendString(string)
        return self.getString()

class OphirPowermeter(object):
    def __init__(self,interchar_timeout=0.1,comPort=0):
        """ Open a serial port for the Ophir power meter and wait for a reply """
        try:
            self.ser = serial.Serial(comPort,9600,timeout=0)
        except:
            raise Exception("Cannot open serial port %d for power meter - aborting" % (comPort,))
        self.interchar_timeout = interchar_timeout
        self.serialTimeout = 5.0
        self.string = ""
        self.tlast = None
        print "Asking Ophir power meter for identification"
        print self.sendCommand("$II\r");            

    def close(self):
        self.ser.close()

    def sendCommand(self,cmd):
        self.ser.write("%s\r" % (cmd,));            
        r = self.waitForString(self.serialTimeout,"Timeout waiting for response to %s" % (cmd,))
        if r[0] != "*": 
            raise Exception,"Error %s in response to %s" % (r,cmd,)
        return r.strip("\r\n")

    def initializeOphir(self):
        print self.sendCommand("$DU 0")
        print self.sendCommand("$CH A")            
        print self.sendCommand("$FP")            
        print self.sendCommand("$HI")            

    def waitForString(self,timeout,msg=""):
        """Wait for a duration up to "timeout" for a string from the serial port. Returns immediately
        if the string arrives before then, and throws an exception if nothing is received"""
        tWait = 0
        while tWait < timeout:
            reply = self.getString()
            if reply != "": 
                return reply
            time.sleep(0.5)
            tWait += 0.5
        else:
            raise IOError(msg)

    def getString(self):
        """Get a string from the serial port. A string either ends with a "\n" or after self.interchar_timeout
        has elapsed since the receipt of the last character"""    
        while True:
            ch = self.ser.read()
            if ch == "": break
            if ch == "\r": continue
            self.string = self.string + ch
            self.tlast = time.clock()
            if ch == "\n":
                result = self.string
                self.string = ""
                self.tlast = None
                return result
        if self.tlast != None and time.clock()-self.tlast > self.interchar_timeout:
            result = self.string
            self.string = ""
            self.tlast = None
            return result
        return ""

class TimeoutException(Exception):
    pass

def CallWithTimeout(timeout,func,*args,**kwargs):
    """ Calls the function func with the specified arguments in a separate thread and returns either when func returns or 
when the timeout expires. The return value of CallWithTimeout is the same as that of func and any exceptions which occur in
func are re-raised. If the timeout occurs, the TimeoutException is raised. """
    class ThreadWithResult(Thread):
        def __init__(self,group=None, target=None, name=None, args=(), kwargs={}):
            Thread.__init__(self,group,name=name,args=args,kwargs=kwargs)
            self.target = target
            self.retVal = None
            self.completed = False
            self.exception = None

        def run(self):
            try:
                self.retVal = self.target(*args, **kwargs)
            except Exception, e:
                self.exception = e
            self.completed = True

    t = ThreadWithResult(target=func,args=args,kwargs=kwargs)
    isinstance(t,ThreadWithResult)
    t.setDaemon(True)
    t.start()
    t.join(timeout)
    if t.completed:
        if t.exception is None:
            return t.retVal
        else:
            raise t.exception
    else:
        raise TimeOutException,"CallWithTimeout timed out after %s seconds" % (timeout,)  

def best_fit(x,y,d):
    p = polyfit(x,y,d)
    y = reshape(y,(-1,))
    y1 = reshape(polyval(p,x),(-1,))
    res = sum((y-y1)**2)/len(y)
    return (p,res,y1)

def best_fit_centered(x,y,d):
    x = array(x)
    mu_x = mean(x)
    sdev_x = std(x)
    xc = (x-mu_x)/sdev_x
    p,res,y1 = best_fit(xc,y,d)
    return (mu_x,sdev_x,p,res,y1)

def verdict(text,value,min,max,fmt):
    from string import ljust
    res = 'FAIL'
    if value>=min and value<=max:
        res = 'pass'
    return ljust((text+" ["+fmt+" , "+fmt+"]")%(min,max),50)+ljust(fmt%value,12)+res

def findcut(x,y,yc):
    """ Given a piecewise linear function whose vertices are specified by the vectors (x,y), find the values of x
at which the function takes on the value yc """
    xc = []
    assert len(x)==len(y), "Vectors x and y in findcut must be of the same length"
    for i in range(len(x)-1):
        if y[i]<=yc<=y[i+1] or y[i]>=yc>=y[i+1]:
            if y[i+1] != y[i]:        
                xc.append(x[i]+(yc-y[i])*(x[i+1]-x[i])/float(y[i+1]-y[i]))
            else:
                xc.append(0.5*(x[i]+x[i+1]))
    return xc        

class GridTable(object):
    "Class for writing out a grid table"
    def __init__(self,columnWidths):
        self.columnWidths = columnWidths
        self.tableEntries = None

    def setEntries(self,tableEntries):
        self.tableEntries = tableEntries

    def writeOut(self,fp):
        rowSep = []
        for w in self.columnWidths:
            rowSep.append(w*'-')
        rowSep = "+" + ("+".join(rowSep)) + "+"
        print >> fp, "\n%s" % rowSep
        for rowEntry in self.tableEntries:
            rowStr = []
            for col in range(len(self.columnWidths)):
                if col<len(rowEntry): entry = rowEntry[col]
                else: entry = ""
                w = self.columnWidths[col]
                if len(entry) <= w:
                    rowStr.append(("%%%ds" % (w,)) % entry)
                else:
                    rowStr.append(w*"X")
            rowStr = "|" + ("|".join(rowStr)) + "|"
            print >> fp, rowStr
            print >> fp, rowSep

class VerdictTable(GridTable):
    "Class for writing a verdict table"
    def __init__(self,columnWidths):
        if isinstance(columnWidths,types.IntType):
            columnWidths = [columnWidths]
        columnWidths += 4*[columnWidths[-1]]
        columnWidths = columnWidths[:5]
        GridTable.__init__(self,columnWidths)
        self.overallResult = 'pass'
        self.failures = []

    def setEntries(self,tableEntries):
        self.tableEntries = [["Parameter","Value","Minimum","Maximum","Verdict"]]
        for entry in tableEntries:
            format = "%s"
            name,value = entry[:2]
            if len(entry)>=3:
                min,max = entry[2:4]
                if len(entry)==5: format = entry[4]
                if value >= min and value <= max: verdict = "Pass"
                else: 
                    verdict = "FAIL"
                    self.overallResult = 'FAIL'
                    self.failures.append(name)
                self.tableEntries.append([name,format%(value,),format%(min,),format%(max,),verdict])
            else:
                if len(entry)==3: format = entry[2]
                self.tableEntries.append([name,format%(value,)])
                
    def giveVerdict(self):
        return self.overallResult
            
    def failureList(self):
        return self.failureList
    
#class VerdictTable(object):
    #"Class for writing a verdict table"
    #def __init__(self,columnWidth):
        #self.columnWidth = columnWidth
        #self.tableEntries = None

    #def writeOut(self,fp):
        #w = self.columnWidth
        #fmt = "%%%ds %%%ds %%%ds %%%ds %%%ds" % (w,w,w,w,w)
        #print >> fp,"\n"+fmt % (w*"=",w*"=",w*"=",w*"=",w*"=")
        #print >> fp,fmt % ("Parameter","Value","Minimum","Maximum","Verdict")
        #print >> fp,fmt % (w*"=",w*"=",w*"=",w*"=",w*"=")
        #for (name,value,min,max,format) in self.tableEntries:
            #if value >= min and value <= max: verdict = "Pass"
            #else: verdict = "FAIL"
            #print >> fp,fmt % (name,(format%(value,)),(format%(min,)),(format%(max,)),verdict,)
        #print >> fp,fmt % (w*"=",w*"=",w*"=",w*"=",w*"=")

class CsvData(object):
    "Class for writing to a comma separated value file"
    def __init__(self):
        self.parameters = {}
        self.columnTitles = []
        self.columnUnits = []

    def protectComma(self,s):
        if s.find(",") < 0: return s
        else: return '"%s"' % s

    def writeOut(self,fp):
        keys = self.parameters.keys()
        keys.sort()
        for key in keys:
            print >> fp, "# %s,%s" % tuple([self.protectComma(s) for s in [key,self.parameters[key]]])
        print
        print >> fp, "# Units,,%s"  % (",".join([self.protectComma(s) for s in self.columnUnits]),)
        print >> fp, "# Titles,,%s" % (",".join([self.protectComma(s) for s in self.columnTitles]),)

class TestParameters(object):
    def __init__(self,engineName,testCode):
        self.parameters = {}
        self.parameters["EngineName"] = engineName
        self.parameters["TestCode"] = testCode
        self.baseDirectory = "C:/testResults/%s/test/" % (engineName,)
        self.parameters["DateTime"] = time.strftime("%Y%m%d_%H%M%S",time.localtime())
        self.relativeTestDirectory = "%s/%s/" % (self.parameters["TestCode"],self.parameters["DateTime"])
        self.absoluteTestDirectory = self.baseDirectory + self.relativeTestDirectory
        os.makedirs(self.absoluteTestDirectory)
        if not os.path.exists(self.baseDirectory + reportFilename):
            fp = file(self.baseDirectory + reportFilename,"wa")
            fp.write(reportTemplate)
            fp.close()
        self.rstFilename = self.absoluteTestDirectory + "rst_file.txt"
        self.rstFile = file(self.rstFilename,"w+a")
        print >> self.rstFile, "\n\n.. ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        print >> self.rstFile, ".. +++ +++ +++ Start of file: %s\n" % (self.rstFilename,)
        title = description[self.parameters["TestCode"]]["Title"]
        print >>self.rstFile,"%s\n%s" % (title,len(title)*'-')
        print >>self.rstFile,":Engine Name: %s" % (self.parameters["EngineName"],)
        print >>self.rstFile,":Test Code: %s" % (self.parameters["TestCode"],)
        print >>self.rstFile,":Date/Time: %s" % (self.parameters["DateTime"],)
        print >>self.rstFile,":Description: %s" % (description[self.parameters["TestCode"]]["Descr"],)

    def appendReport(self):
        fp = file(self.baseDirectory + reportFilename,"a")
        print >> fp, "\n.. include:: %s" % self.rstFilename
        fp.close()

    def makeHTML(self): 
        self.rstFile.close()
        os.system(r'"c:\Program Files\docutils\tools\rst2html.py" ' + self.baseDirectory + 
                  reportFilename + ' ' + self.baseDirectory + htmlReportFilename)

if __name__ == "__main__":
    tp = TestParameters("002_Alpha","200001")
    tp.appendReport()
    tp.makeHTML()
