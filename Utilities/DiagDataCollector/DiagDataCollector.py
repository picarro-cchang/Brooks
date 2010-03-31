#!/usr/bin/python
#
# File Name: DiagDataCollector.py
# Purpose: Collect instrument diagnositc data files from database
#
# File History:
# 10-01-25 alex  Created

import sys
import os
import sqlite3
import tables
import wx
import threading
from datetime import datetime, timedelta 
from DiagDataCollectorFrame import DiagDataCollectorFrame
from Host.autogen import interface
from Host.Common import timestamp
from Host.Common.CustomConfigObj import CustomConfigObj

APP_NAME = "DiagDataCollector"
DEFAULT_CONFIG_NAME = "DiagDataCollector.ini"
MAX_LEVEL = 4  # 0,1,...,MAX_LEVEL

STREAM_NUM_TO_NAME_DICT = {}
for streamNum in interface.STREAM_MemberTypeDict:
    STREAM_NUM_TO_NAME_DICT[streamNum] = interface.STREAM_MemberTypeDict[streamNum][7:]

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

class DiagDataCollector(DiagDataCollectorFrame):
    def __init__(self, configFile, *args, **kwds):
        DiagDataCollectorFrame.__init__(self, *args, **kwds)
        
        co = CustomConfigObj(configFile)
        self.targetFilePrefix = co.get("Main", "targetFilePrefix", "C:/UserData/Diag")
        self.instName = co.get("Main", "instName", "CRDS")
        self.useUTC = co.getboolean("Main", "useUTC", "True")
        dbFilename = co.get("Main", "dbFilename")
        self.dbCon = sqlite3.connect(dbFilename)
        self.filters = tables.Filters(complevel=1, fletcher32=True)
        colDict = {"time":tables.Int64Col(), "date_time":tables.Int64Col(), "idx":tables.Int32Col()}
        for streamName in STREAM_NUM_TO_NAME_DICT.values():
            colDict[streamName] = tables.Float32Col(shape=(3,))
        self.TableType = type("TableType",(tables.IsDescription,),colDict)
        self.h5 = None
        self.table = None
        self.timeLimits = None
        
        # Bind button event
        self.Bind(wx.EVT_BUTTON, self.onGetFile, self.buttonGetFile)
        # Bind URL to message box
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrlMsg) 
        
        self.textCtrlMsg.SetValue("Select date and time to retrieve diagnostic data files\n")

    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlMsg.GetRange(event.GetURLStart()+5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()
            
    def onGetFile(self, event):
        self.startDatetime = self._convToDatetime(self.ctrlStartDate.GetValue(), self.ctrlStartTime.GetValue())
        dataDurHrs = float(self.spinCtrlDataDur.GetValue())
        diff = timedelta(hours=dataDurHrs)
        self.endDatetime = min(datetime.now(), self.startDatetime + diff)
        if self.useUTC:
            offset = datetime.utcnow() - datetime.now()
            self.startDatetime += offset
            self.endDatetime += offset
        startTimestamp = timestamp.datetimeToTimestamp(self.startDatetime)
        endTimestamp = timestamp.datetimeToTimestamp(self.endDatetime)

        self.timeLimits = [startTimestamp, endTimestamp]
        self._createH5File()
        # Threading is not allowed in SQLite!
        self._writeH5File()
        
    def _convToDatetime(self, wxDate, timeStr): 
        return datetime.strptime("%s-%s-%s %s" % (wxDate.GetYear(), wxDate.GetMonth()+1, wxDate.GetDay(), timeStr),
                                          "%Y-%m-%d %H:%M:%S")
         
    def _createH5File(self):
        if self.table != None:
            self.table.flush()
        if self.h5 != None:
            self.h5.close()
        startTime = datetime.strftime(self.startDatetime, "%Y%m%d%H%M%S")
        endTime = datetime.strftime(self.endDatetime, "%Y%m%d%H%M%S")
        self.h5Filename = "%s_%s_%s_%s.h5" % (self.targetFilePrefix, self.instName, startTime, endTime)
        try:
            self.h5 = tables.openFile(self.h5Filename, mode="w", title="CRDS Diagnostic Data File")
        except Exception, err:
            print err
            self.h5 = None
        self.table = None
        
    def _closeH5File(self):
        if self.table != None:
            self.table.flush()
        if self.h5 != None:
            self.h5.close()
        self.h5 = None
        self.table = None
        self.timeLimits = None
        
    def _writeH5File(self):
        if self.h5 != None and self.timeLimits != None:
            for level in range(MAX_LEVEL+1):
                values = self.dbCon.execute(
                    "select time,idx,streamNum,value,minVal,maxVal from history" +
                    " where level=? and time >= ? and time <= ?",
                    (level, self.timeLimits[0], self.timeLimits[1])).fetchall()
                dataDict = {}
                if len(values) > 0:
                    for data in values:
                        dTime = data[0]
                        idx = data[1]
                        if idx not in dataDict:
                            dataDict[idx] = {"time":dTime}
                        else:
                            dataDict[idx]["time"] = max(dataDict[idx]["time"], dTime)
                        dataDict[idx][STREAM_NUM_TO_NAME_DICT[data[2]]] = tuple(data[3:])
                        dataDict[idx]["date_time"] = timestamp.unixTime(dataDict[idx]["time"])
                    self.table = self.h5.createTable("/", "DiagData_%dSec" % 10**level, self.TableType, filters=self.filters)
                    row = self.table.row
                    for idx in dataDict:
                        for key in dataDict[idx]:
                            row[key] = dataDict[idx][key]
                        row["idx"] = idx
                        row.append()
                    self.table.flush()
            self.textCtrlMsg.SetValue("Output file:\nfile:%s\n" % os.path.abspath(self.h5Filename))
            self._closeH5File()
        else:
            self.textCtrlMsg.SetValue("Unable to create output file\n")

HELP_STRING = \
"""

DiagDataCollector.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile
    
if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = DiagDataCollector(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()