"""
File name: KMLConverter.py
Purpose: Post-process .dat files to create .kml files

File History:
    2011-07-06 Eric Balkanski Created the original software
               Alex Lee       Re-wrote and created the GUI and wrapper
"""

import os
import sys
import wx
import threading
import getopt
import time
from KMLConverterFrame import KMLConverterFrame
from Host.Common.CustomConfigObj import CustomConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "PicarroKML.ini"

# kml formatting
KML_OPEN_TEMPLATE = \
"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
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

KML_CLOSE_TEMPLATE = """
</Document>
</kml>
"""

class ConvertKML(object):
    def __init__(self, datafile, textCtrlMsg, outputDir = ""):
        self.datafile = datafile
        self.textCtrlMsg = textCtrlMsg
        if outputDir:
            self.outputDir = outputDir
        else:
            self.outputDir = os.path.split(datafile)[0]
        fd = open(datafile, "r")
        lines = fd.readlines()
        fd.close()
        self.data = []
        self.titleList = lines[0].split()
        requiredLen = len(self.titleList)
        for line in lines[1:]:
            if len(line.split()) >= requiredLen:
                self.data.append(line.split())
                
    def _getTime(self, format=0):
        if format == 0:
            return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        else:
            return time.strftime("%Y%m%d%H%M%S", time.localtime())
            
    def convert(self, concList, gpsList, colorList, baselineList, multiplierList, shiftConcSamples=0):
        # if self.shiftConcSamples < 0 - align concs to earlier GPS
        # if self.shiftConcSamples > 0 - align concs to later GPS
        concIdxList = [self.titleList.index(i) for i in concList]
        gpsIdxList = [self.titleList.index(i) for i in gpsList]
        numConcs = len(concList)
        timestamp = self._getTime(1)
        if os.path.isdir(self.outputDir):
            kmlFilename = os.path.join(self.outputDir, os.path.split(self.datafile)[1].replace(".dat", "_PostProcessed_%s.kml" % (timestamp,)))
        else:
            kmlFilename = os.path.split(self.datafile)[1].replace(".dat", "_PostProcessed_%s.kml" % (timestamp,))

        stackList = []
        for i in range(numConcs):
            kmlBlock = []
            for l in range(len(self.data)):
                if shiftConcSamples <= 0 and l >= -1*shiftConcSamples:
                    # Current Conc with older GPS
                    try:
                        kmlLine = '%s,%s,%f\n' % (self.data[l+shiftConcSamples][gpsIdxList[1]],self.data[l+shiftConcSamples][gpsIdxList[0]],(float(self.data[l][concIdxList[i]]) - baselineList[i]) * multiplierList[i])
                        kmlBlock.append(kmlLine)
                    except:
                        pass
                elif shiftConcSamples > 0 and l >= shiftConcSamples:
                    # Current GPS with older Conc
                    try:
                        kmlLine = '%s,%s,%f\n' % (self.data[l][gpsIdxList[1]],self.data[l][gpsIdxList[0]],(float(self.data[l-shiftConcSamples][concIdxList[i]]) - baselineList[i]) * multiplierList[i])
                        kmlBlock.append(kmlLine)
                    except:
                        pass
            stackList.append("".join(kmlBlock))

        out = open(kmlFilename,'w')
        out.flush()
        
        # KML_OPEN_TEMPLATE
        out.write(KML_OPEN_TEMPLATE)
        
        # KML_BODY_TEMPLATE % (index, baseline, multiplier, index, color, color, conc, index, body)
        for i in range(numConcs):
            out.write(KML_BODY_TEMPLATE % (i, baselineList[i], multiplierList[i], i, colorList[i], colorList[i], concList[i], i, stackList[i]))
        
        # KML_CLOSE_TEMPLATE
        out.write(KML_CLOSE_TEMPLATE)
        out.close()

        return kmlFilename
        
class KMLConverter(KMLConverterFrame):
    def __init__(self, configFile, *args, **kwds):
        self.cp = CustomConfigObj(configFile)
        self.outputDir = self.cp.get("PostProcess", "outputDir", "C:/Picarro/KML_Files")
        self.shiftConcSamples = self.cp.getint("PostProcess", "shiftConcSamples", 0)
        self.concList = [c.strip() for c in self.cp.get("Main", "concList").split(",")]
        self.gpsList = [c.strip() for c in self.cp.get("Main", "gpsList").split(",")]
        if len(self.gpsList) != 2:
            self.gpsList = ["GPS_ABS_LAT", "GPS_ABS_LONG"]
        self.colorList = [c.strip() for c in self.cp.get("Main", "colorList").split(",")]
        self.baselineList = [float(c) for c in self.cp.get("Main", "baselineList").split(",")]
        self.multiplierList = [float(c) for c in self.cp.get("Main", "multiplierList").split(",")]
        KMLConverterFrame.__init__(self, *args, **kwds)
        self.defaultPath = None
        self.filenames = []
        self.converters = []
        self.bindEvents()
        
    def bindEvents(self):       
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, self.iLoadFile)
        self.Bind(wx.EVT_MENU, self.onOutDirMenu, self.iOutDir)
        self.Bind(wx.EVT_MENU, self.onShiftMenu, self.iShift)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_BUTTON, self.onProcButton, self.procButton)              
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton) 
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrlMsg) 
        self.Bind(wx.EVT_CLOSE, self.onCloseButton)
        
    def onOutDirMenu(self, event):
        d = wx.DirDialog(None,"Specify the output directory for the converted KML files", style=wx.DD_DEFAULT_STYLE,
                         defaultPath=self.outputDir)
        if d.ShowModal() == wx.ID_OK:
            self.outputDir = d.GetPath().replace("\\", "/")
            self.cp.set("PostProcess", "outputDir", self.outputDir)
            self.cp.write()

    def onShiftMenu(self, event):
        d = wx.NumberEntryDialog(None,"Specify the number of shifting samples\n-N => Align current concentrations with GPS N samples ago\n+N => Align current GPS with concentrations N samples ago", 
            "Number of shifting samples", "Number of shifting samples", self.shiftConcSamples, -1000, 1000)
        if d.ShowModal() == wx.ID_OK:
            self.shiftConcSamples = d.GetValue()
            self.cp.set("PostProcess", "shiftConcSamples", self.shiftConcSamples)
            self.cp.write()
            
    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlMsg.GetRange(event.GetURLStart()+5, event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()
        
    def onProcButton(self, evt):
        if not self.converters:
            return
        self.textCtrlMsg.WriteText("Converting...\n")
        procThread = threading.Thread(target = self.procFiles)
        procThread.setDaemon(True)
        procThread.start()
        
    def onCloseButton(self, evt):
        sys.exit(0)
        self.Destroy()
        
    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, "All rights reserved.\n\nVersion: 1.0.0\n\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Picarro KML Converter", wx.OK)
        d.ShowModal()
        d.Destroy()

    def onLoadFileMenu(self, evt):
        if not self.defaultPath:
            self.defaultPath = os.getcwd()
        dlg = wx.FileDialog(self, "Select Data File or Directory...",
                            self.defaultPath, wildcard = "*.dat", style=wx.OPEN|wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filenames = dlg.GetPaths()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        self.defaultPath = dlg.GetDirectory()
        self.converters = []
        self.textCtrlMsg.Clear()
        self.textCtrlMsg.WriteText("Loading...\n")
        loadThread = threading.Thread(target = self.loadFiles)
        loadThread.setDaemon(True)
        loadThread.start()

    def procFiles(self):
        self.enableAll(False)
        outList = []
        for c in self.converters:
            try:
                outList.append(c.convert(self.concList, self.gpsList, self.colorList, self.baselineList, self.multiplierList, self.shiftConcSamples))
            except Exception, err:
                self.textCtrlMsg.WriteText("Exception! %r\n" % err)
        if outList:
            self.textCtrlMsg.WriteText("Conversion Completed:\n")
            for filename in outList:
                self.textCtrlMsg.WriteText("file:%s\n" % filename)
        self.enableAll(True)

    def loadFiles(self):
        self.enableAll(False)
        for filename in self.filenames:
            self.converters.append(ConvertKML(filename, self.textCtrlMsg, self.outputDir))
            self.textCtrlMsg.WriteText("%s\n" % filename)
        self.enableAll(True)
        
    def enableAll(self, onFlag):
        if onFlag:
            self.iLoadFile.Enable(True)
            self.iAbout.Enable(True)
            self.procButton.Enable(True)
            self.closeButton.Enable(True)
        else:
            self.iLoadFile.Enable(False)
            self.iAbout.Enable(False)
            self.procButton.Enable(False)
            self.closeButton.Enable(False)
            
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

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME
    
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    return configFile
    
if __name__ == "__main__" :
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    configFile = handleCommandSwitches()
    frame = KMLConverter(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()