"""
File Name: PicarroKML.py
Purpose:
    Create KML files  to display geographic concentration data on Google Earth

File History:
    10-07-10 Alex  Converted Matt's Gen 1 version to G2000 format
    12-17-10 Alex  Integrate this module into G2000 package

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import os
import sys
import wx
import threading
import getopt
import time
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DATA_MANAGER, RPC_PORT_ARCHIVER
from Host.Common.CustomConfigObj import CustomConfigObj
from collections import deque

CRDS_DataManager = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "PicarroKML")
CRDS_Archiver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_ARCHIVER, ClientName = "PicarroKML", IsDontCareConnection = False)

# kml formatting
KML_OPEN_TEMPLATE = \
"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <LookAt>
      <longitude>%s</longitude>
      <latitude>%s</latitude>
      <range>%s</range>
      <tilt>%s</tilt>
      <heading>%s</heading>
    </LookAt>
"""

# To use template: kmlXXX = KML_BODY_TEMPLATE % (index, baseline, multiplier, index, color, color, conc, index, body)
KML_BODY_TEMPLATE = """
<!-- Instrument Trace #%d-->
<!-- baseline = %s-->
<!-- multiplier = %s-->

    <Style id="lineStyle%d">
        <LineStyle>
            <color>%s</color>
            <width>3</width>
        </LineStyle>
        <PolyStyle>
            <color>%s</color>
        </PolyStyle>
    </Style>

    <Placemark>
        <name>Picarro Instrument Trace - %s</name>
        <styleUrl>lineStyle%d</styleUrl>
        <LineString>
            <extrude>1</extrude>
            <tessellate>1</tessellate>
            <altitudeMode>relativeToGround</altitudeMode>
            <coordinates>
            %s
            </coordinates>
        </LineString>
    </Placemark>
"""

KML_CLOSE = """
</Document>
</kml>
"""

# San Fran Latitude, Longitude: 37.7749295, -122.4194155
# KML: -122.014557,37.353230,520.304443

class CameraCtrlGui(wx.Dialog):
    def __init__(self, defaults, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.panel_1 = wx.Panel(self, -1)
        self.panel_2 = wx.Panel(self, -1)
        labels =["Range", "Tilt", "Heading"]
        self.numParams = len(labels)
        self.labelList = []
        self.textCtrlList = []
        for i in range(self.numParams):
            self.labelList.append(wx.StaticText(self.panel_2, -1, labels[i]))
            self.textCtrlList.append(wx.TextCtrl(self.panel_2, -1, defaults[i]))
        self.okButton = wx.Button(self.panel_1, wx.ID_OK, "")
        self.cancelButton = wx.Button(self.panel_1, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetTitle("Google Earth Camera Control")
        for textCtrl in self.textCtrlList:
            textCtrl.SetMinSize((200, -1))

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1 = wx.FlexGridSizer(self.numParams, 2, 10, 10)
        grid_sizer_1.Add(self.labelList[0], 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlList[0], 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 10)
        for idx in range(1,self.numParams):
            grid_sizer_1.Add(self.labelList[idx], 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10)
            grid_sizer_1.Add(self.textCtrlList[idx], 1, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 10)
        self.panel_2.SetSizer(grid_sizer_1)
        grid_sizer_1.AddGrowableCol(1)
        sizer_1.Add(self.panel_2, 1, wx.EXPAND, 0)
        sizer_2.Add((20, 20), 1, 0, 0)
        sizer_2.Add(self.okButton, 0, wx.TOP|wx.BOTTOM, 15)
        sizer_2.Add((20, 40), 0, 0, 0)
        sizer_2.Add(self.cancelButton, 0, wx.TOP|wx.BOTTOM|wx.RIGHT, 15)
        #sizer_2.Add((20, 20), 1, 0, 0)
        self.panel_1.SetSizer(sizer_2)
        sizer_1.Add(self.panel_1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

class PicarroKMLFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.SetTitle("Picarro KML Tool")
        self.SetBackgroundColour("#E0FFFF")
        self.labelTitle = wx.StaticText(self, -1, "Picarro KML Tool", style=wx.ALIGN_CENTRE)
        self.labelTitle.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))

        # Menu bar
        self.frameMenubar = wx.MenuBar()

        self.iSettings = wx.Menu()
        self.frameMenubar.Append(self.iSettings,"Settings")
        self.iCameraCtrl = wx.MenuItem(self.iSettings, wx.NewId(), "Camera Control", "", wx.ITEM_NORMAL)
        self.iSettings.AppendItem(self.iCameraCtrl)

        self.iHelp = wx.Menu()
        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "Picarro KML Tool", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)

        self.SetMenuBar(self.frameMenubar)

        # Other graphical components
        self.staticLine = wx.StaticLine(self, -1)
        self.labelFooter = wx.StaticText(self, -1, "Copyright Picarro, Inc. 1999-%d" % time.localtime()[0], style=wx.ALIGN_CENTER)
        self.labelOutputPath = wx.StaticText(self, -1, "Output KML File")
        self.textCtrlOutputPath = wx.TextCtrl(self, -1, "", style = wx.TE_READONLY)
        self.textCtrlOutputPath.SetMinSize((450,20))
        self.labelStatus = wx.StaticText(self, -1, "Status (last 20 lines)")
        self.textCtrlStatus = wx.TextCtrl(self, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrlStatus.SetMinSize((560,275))

        # Buttons
        self.buttonStart = wx.Button(self, -1, "Start", style=wx.BU_EXACTFIT)
        self.buttonStop = wx.Button(self, -1, "Stop", style=wx.BU_EXACTFIT)
        self.buttonExit = wx.Button(self, -1, "Exit", style=wx.BU_EXACTFIT)
        self.buttonStart.SetMinSize((157, 25))
        self.buttonStart.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonStart.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonStop.SetMinSize((157, 25))
        self.buttonStop.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonStop.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonExit.SetMinSize((157, 25))
        self.buttonExit.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonExit.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(0, 2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_1.SetMinSize((550,100))
        sizer_1.Add(self.labelTitle, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND|wx.BOTTOM, 5)

        grid_sizer_1.Add(self.labelOutputPath, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_1.Add(self.textCtrlOutputPath, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)

        sizer_2.Add(self.labelStatus, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_2.Add((-1,5))
        sizer_2.Add(self.textCtrlStatus, 0, wx.LEFT|wx.RIGHT, 10)

        sizer_3.Add(self.buttonStart, 1, wx.LEFT|wx.RIGHT, 10)
        sizer_3.Add(self.buttonStop, 1, wx.LEFT|wx.RIGHT, 10)
        sizer_3.Add(self.buttonExit, 1, wx.LEFT|wx.RIGHT, 10)

        sizer_1.Add(grid_sizer_1, 0, wx.BOTTOM, 10)
        sizer_1.Add(sizer_2, 0, wx.BOTTOM, 20)
        sizer_1.Add(sizer_3, 0, wx.BOTTOM, 20)
        sizer_1.Add(self.labelFooter, 0, wx.EXPAND| wx.BOTTOM, 5)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

class PicarroKML(PicarroKMLFrame):
    def __init__(self, configFile, *args, **kwds):
        self.cp = CustomConfigObj(configFile)
        self.outputDir = self.cp.get("Main", "outputDir", "C:/Picarro/KML_Files")
        self.concList = [c.strip() for c in self.cp.get("Main", "concList").split(",")]
        self.gpsList = [c.strip() for c in self.cp.get("Main", "gpsList").split(",")]
        if len(self.gpsList) != 2:
            self.gpsList = ["GPS_ABS_LAT", "GPS_ABS_LONG"]
        self.colorList = [c.strip() for c in self.cp.get("Main", "colorList").split(",")]
        self.baselineList = [float(c) for c in self.cp.get("Main", "baselineList").split(",")]
        self.multiplierList = [float(c) for c in self.cp.get("Main", "multiplierList").split(",")]
        self.source = self.cp.get("Main", "sourcescript")
        self.archiveGroupName = self.cp.get("Main", "archiveGroupName", "")
        self.maxNumLines = self.cp.getint("Main", "maxNumLines", 1000)
        self.shiftConcSamples = self.cp.getint("Main", "shiftConcSamples", 0)
        self.numConcs = len(self.concList)
        self.delayedBuffer = {}
        if self.shiftConcSamples < 0:
            # Align concs to earlier GPS - add GPS to buffer
            for label in self.gpsList:
                self.delayedBuffer[label] = deque()
        elif self.shiftConcSamples > 0:
            # Align concs to later GPS - add concs to buffer
            for label in self.concList:
                self.delayedBuffer[label] = deque()

        self.stop = True
        self.statusMessage = []
        #picarro instrument connection
        self.completeList = self.concList + self.gpsList
        CRDS_DataManager.MeasBuffer_Set(self.source, self.completeList, 50)
        PicarroKMLFrame.__init__(self, *args, **kwds)
        self.bindEvents()
        self.buttonStart.Enable(True)
        self.buttonStop.Enable(False)
        self.datFilename = []
        self.kmlFilename = []
        self.range = self.cp.get("Camera", "range", "5000")
        self.tilt = self.cp.get("Camera", "tilt", "30")
        self.heading = self.cp.get("Camera", "heading", "0")

    def bindEvents(self):
        self.Bind(wx.EVT_BUTTON, self.onStartButton, self.buttonStart)
        self.Bind(wx.EVT_BUTTON, self.onStopButton, self.buttonStop)
        self.Bind(wx.EVT_BUTTON, self.onClose, self.buttonExit)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_MENU, self.onCameraCtrl, self.iCameraCtrl)

    def onStartButton(self, evt):
        self.stop = False
        launchCoordinatorThread = threading.Thread(target = self._start)
        launchCoordinatorThread.setDaemon(True)
        launchCoordinatorThread.start()
        self.buttonStart.Enable(False)
        self.buttonStop.Enable(True)

    def onStopButton(self, evt):
        self.stop = True

    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, "All rights reserved.\n\nVersion: 1.0.0\n\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc. (http://www.picarro.com)", "About Picarro KML Tool", wx.OK)
        d.ShowModal()
        d.Destroy()

    def onClose(self, evt):
        d = wx.MessageDialog(None, "Terminate Picarro KML Tool now?\n\nSelect \"Yes\" to terminate this program.\nSelect \"No\" to cancel this action.",\
                        "Exit Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
        if d.ShowModal() != wx.ID_YES:
            d.Destroy()
            return
        else:
            d.Destroy()
        self.Destroy()

    def onCameraCtrl(self, evt):
        d = CameraCtrlGui([self.range, self.tilt, self.heading], None, -1, "")
        getCtrl = (d.ShowModal() == wx.ID_OK)
        if getCtrl:
            self.range = d.textCtrlList[0].GetValue()
            self.tilt = d.textCtrlList[1].GetValue()
            self.heading = d.textCtrlList[2].GetValue()
        d.Destroy()
        self.cp.set("Camera", "range", self.range)
        self.cp.set("Camera", "tilt", self.tilt)
        self.cp.set("Camera", "heading", self.range)
        self.cp.write()


    def _getTime(self, format=0):
        if format == 0:
            return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        else:
            return time.strftime("%Y%m%d%H%M%S", time.localtime())

    def _writeToStatus(self, message):
        self.statusMessage.append("%s   %s\n" % (self._getTime(), message,))
        self.statusMessage = self.statusMessage[-20:]
        self.textCtrlStatus.SetValue("".join(self.statusMessage))

    def _createFilename(self):
        timestamp = self._getTime(1)
        self.datFilename = []
        for i in range(self.numConcs):
            conc = self.concList[i]
            if os.path.isdir(self.outputDir):
                datFilename = os.path.join(self.outputDir, "PicarroGIS-%s-%s.dat" % (timestamp, conc))
            else:
                try:
                    os.makedirs(self.outputDir)
                    datFilename = os.path.join(self.outputDir, "PicarroGIS-%s-%s.dat" % (timestamp, conc))
                except:
                    datFilename = "PicarroGIS-%s-%s.dat" % (timestamp, conc)
            self.datFilename.append(datFilename)

        if os.path.isdir(self.outputDir):
            self.kmlFilename = os.path.join(self.outputDir, "PicarroGIS-%s-%s.kml" % (timestamp, "-".join(self.concList)))
        else:
            self.kmlFilename = "PicarroGIS-%s-%s.kml" % (timestamp, "-".join(self.concList))
        self.textCtrlOutputPath.SetValue(os.path.abspath(self.kmlFilename))

    def _start(self):
        self._createFilename()
        self._writeToStatus("Picarro KML Tool starting")

        for i in range(self.numConcs):
            datout = open(self.datFilename[i],'w')
            datout.flush()
            datout.close()

        CRDS_DataManager.MeasBuffer_Clear()
        numLines = 0
        bufferSize = 0
        while not self.stop:
            try:
                reply = CRDS_DataManager.MeasBuffer_GetFirst()
                if not reply:
                    time.sleep(0.5)
                    continue

                for i in range(len(self.concList)):
                    label = self.concList[i]
                    try:
                        reply[label] = (reply[label] - self.baselineList[i]) * self.multiplierList[i]
                    except:
                        pass

                if self.shiftConcSamples < 0:
                    for label in self.gpsList:
                        self.delayedBuffer[label].append(reply[label])
                elif self.shiftConcSamples > 0:
                    for label in self.concList:
                        self.delayedBuffer[label].append(reply[label])

                if bufferSize < abs(self.shiftConcSamples):
                    bufferSize += 1
                    continue

                valueList = []
                if self.shiftConcSamples == 0:
                    for label in self.completeList:
                        valueList.append(reply[label])
                elif self.shiftConcSamples < 0:
                    for label in self.concList:
                        valueList.append(reply[label])
                    for label in self.gpsList:
                        valueList.append(self.delayedBuffer[label][0])
                        self.delayedBuffer[label].popleft()
                elif self.shiftConcSamples > 0:
                    for label in self.concList:
                        valueList.append(self.delayedBuffer[label][0])
                        self.delayedBuffer[label].popleft()
                    for label in self.gpsList:
                        valueList.append(reply[label])

                valueStrList = [str(val) for val in valueList]
                labelStr = ", ".join(self.completeList)
                valueStr = ", ".join(valueStrList)
                self._writeToStatus('%s = %s' % (labelStr, valueStr))

                stackList = []
                newLat = 0.0
                newLong = 0.0
                for i in range(self.numConcs):
                    conc = self.concList[i]
                    datout = open(self.datFilename[i],'a')
                    datout.write('%f,%f,%f\n' % (valueList[-1],valueList[-2],valueList[i]))
                    datout.close()
                    newLat = valueList[-2]
                    newLong = valueList[-1]

                    datout = open(self.datFilename[i],'r')
                    stackList.append(datout.read())
                    datout.close()
                    numLines += 1

                out = open(self.kmlFilename,'w')
                out.flush()

                # KML_OPEN_TEMPLATE
                out.write(KML_OPEN_TEMPLATE % (newLong, newLat, self.range, self.tilt, self.heading))

                # KML_BODY_TEMPLATE % (index, baseline, multiplier, index, color, color, conc, index, body)
                for i in range(self.numConcs):
                    out.write(KML_BODY_TEMPLATE % (i, self.baselineList[i], self.multiplierList[i], i, self.colorList[i], self.colorList[i], self.concList[i], i, stackList[i]))
                out.write(KML_CLOSE)
                out.close()

                if numLines >= self.maxNumLines:
                    print "Archiving..."
                    if self.archiveGroupName:
                        for i in range(self.numConcs):
                            self._writeToStatus("Archiving %s" % (self.datFilename[i],))
                            try:
                                CRDS_Archiver.ArchiveFile(self.archiveGroupName, self.datFilename[i], removeOriginal=True)
                            except Exception, err:
                                print "%r" % err

                        self._writeToStatus("Archiving %s" % (self.kmlFilename,))
                        try:
                            CRDS_Archiver.ArchiveFile(self.archiveGroupName, self.kmlFilename, removeOriginal=True)
                        except Exception, err:
                            print "%r" % err

                        self._createFilename()
                        numLines = 0

            # instrument will throw index errors when it runs out of data buffer

            except IndexError:
                time.sleep(0.5)

            except Exception, err:
                self._writeToStatus("%r" % (err,))
                time.sleep(0.5)

        self._writeToStatus("Picarro KML Tool stopped")

        self.buttonStart.Enable(True)
        self.buttonStop.Enable(False)

def handleCommandSwitches():
    shortOpts = "c:"
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

if __name__ == "__main__" :
    configFile = handleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = PicarroKML(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()