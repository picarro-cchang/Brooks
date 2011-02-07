"""
File name: DeltaCorrProcessor.py
Purpose: Post-process output data from discrete sample (batch mode) system
"""

import os
import sys
import getopt
import wx

COLUMN_FORMAT = "%7s,%10s,%15s,%15s,%17s,%17s,%16s,%16s,%19s,%19s,%18s,%18s,%21s,%21s,%14s,%15s,%15s\n"

class DeltaCorrProcessorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.STAY_ON_TOP|wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Sample Delta Correction")
        self.SetMinSize((270,100))
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.labelFooter = wx.StaticText(self.panel1, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        self.iFile = wx.Menu()
        self.iHelp = wx.Menu()
        self.frameMenubar.Append(self.iFile,"File")
        self.idLoadFile = wx.NewId()
        self.iLoadFile = wx.MenuItem(self.iFile, self.idLoadFile, "Load data file (.csv)", "", wx.ITEM_NORMAL)
        self.iFile.AppendItem(self.iLoadFile)
        self.idOutDir = wx.NewId()
        self.iOutDir = wx.MenuItem(self.iFile, self.idOutDir, "Select output directory", "", wx.ITEM_NORMAL)
        self.iFile.AppendItem(self.iOutDir)
        self.frameMenubar.Append(self.iHelp,"Help")
        self.idAbout = wx.NewId()
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Sample Delta Correction", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)

        self.textCtrl = wx.TextCtrl(self.panel1, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrl.SetMinSize((250, 80))        

        self.applyButton = wx.Button(self.panel1, -1, "Apply Correction", size=(115,20))
        self.closeButton = wx.Button(self.panel1, wx.ID_CLOSE, "", size=(115,20))
        self.applyButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.closeButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.__do_layout()
        self.bindEvents()
        self.defaultPath = os.getcwd()
        self.defaultOutPath = os.getcwd()
        self.outputDir = ""
        self.filename = ""
        self.stdDelta = None
        self.updateTextCtrl()
        self.applyButton.Enable(False)
        
    def bindEvents(self):       
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, self.iLoadFile)
        self.Bind(wx.EVT_MENU, self.onOutDirMenu, self.iOutDir)
        self.Bind(wx.EVT_MENU, self.onAboutMenu, self.iAbout)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.applyButton)       
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.closeButton) 
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrl)
    
    def onApplyButton(self, event):
        if not self.filename:
            dlg = wx.MessageDialog(None,"Please select input file       ", "Error", style=wx.ICON_EXCLAMATION|wx.STAY_ON_TOP|wx.OK)
            confirm = (dlg.ShowModal() == wx.ID_OK)
            if confirm:
                dlg.Destroy()
                return
        if not self.outputDir:
            dlg = wx.MessageDialog(None,"Please select output directory     ", "Error", style=wx.ICON_EXCLAMATION|wx.STAY_ON_TOP|wx.OK)
            confirm = (dlg.ShowModal() == wx.ID_OK)
            if confirm:
                dlg.Destroy()
                return
        proc = DeltaCorrProcessor(self.outputDir)
        proc.setFilename(self.filename)
        proc.procData()
        if os.path.isfile(proc.getoOutputFilename()):
            self.textCtrl.SetValue("Output file:\nfile:%s\n" % proc.getoOutputFilename())
        else:
            self.textCtrl.SetValue("Failed to create output file")
            
    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, "This application applies standard delta offset to correct sample delta values.\n\nCopyright 1999-2010 Picarro Inc. All rights reserved.\nVersion: 0.01\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Discrete Sample Delta Correction", wx.OK)
        d.ShowModal()
        d.Destroy()
        
    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrl.GetRange(event.GetURLStart()+5, event.GetURLEnd())
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()

    def onLoadFileMenu(self, evt):
        dlg = wx.FileDialog(self, "Select Data File...",
                            self.defaultPath, wildcard = "*.csv", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
            self.defaultPath = dlg.GetDirectory()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.updateTextCtrl()

    def onOutDirMenu(self, evt):
        dlg = wx.DirDialog(self, "Select Output Directory...",
                           self.defaultOutPath)
        if dlg.ShowModal() == wx.ID_OK:
            self.outputDir = dlg.GetPath()
            self.defaultOutPath = self.outputDir
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.updateTextCtrl()

    def onCloseButton(self, evt):
        sys.exit(0)
        self.Destroy()
        
    def updateTextCtrl(self):
        msg1 = "1. Load data file (.csv)"
        msg2 = "2. Select output directory"
        if self.filename:
            msg1 += ("\n= %s" % (self.filename))
        if self.outputDir:
            msg2 += ("\n= %s" % (self.outputDir))
        self.textCtrl.SetValue("Before applying correction, please:\n%s\n%s"% (msg1, msg2))
        if self.filename and self.outputDir:
            self.applyButton.Enable(True)
    
    def __do_layout(self):
        grid_sizer_1 = wx.FlexGridSizer(-1, 2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1.Add(self.applyButton, 0, wx.ALL, 5)
        grid_sizer_1.Add(self.closeButton, 0, wx.ALL, 5)
        sizer_2.Add(self.textCtrl, 0, wx.ALL, 10)
        sizer_2.Add(grid_sizer_1, 0, wx.LEFT, 10)
        sizer_2.Add(self.labelFooter, 0, wx.EXPAND| wx.BOTTOM, 5)
        self.panel1.SetSizer(sizer_2)
        sizer_3.Add(self.panel1, 0, wx.EXPAND, 0)
        self.SetSizer(sizer_3)
        sizer_3.Fit(self)
        self.Layout()
        
class DeltaCorrProcessor():
    def __init__(self, dirname=""):
        self.outputDir = dirname
        self.filepath = ""
        self.outputFilename = ""
    
    def setFilename(self, filepath):
        self.filepath = filepath
           
    def getoOutputFilename(self):
        return self.outputFilename
        
    def procData(self):
        if not self.filepath:
            return
        if not self.outputDir:
            self.outputDir = os.path.dirname(self.filepath)
        self.outputFilename = os.path.abspath(os.path.join(self.outputDir, os.path.basename(self.filepath).split(".")[0] + "_Processed.csv"))
        try:
            fd = open(self.filepath, "r")
            newLines = fd.readlines()
            header = newLines[0]
            measData = newLines[1:]
            fd.close()                
        except Exception, errMsg:
            print errMsg
            return

        sampleBagList = []
        standardList = []
        sampleBlock = []
        firstStandardFound = False
        colFormat = COLUMN_FORMAT
        for line in measData:
            parsedLine = line.split(",")
            if len(parsedLine) !=17:
                continue

            for idx in range(len(parsedLine)):
                parsedLine[idx] = parsedLine[idx].strip()

            if firstStandardFound:
                if parsedLine[4]:
                    sampleBlock.append(parsedLine)
                elif parsedLine[8]:
                    standardList.append(parsedLine)
                    sampleBagList.append(sampleBlock)
                    sampleBlock = []
            else:
                if parsedLine[8]:
                    firstStandardFound = True
                    standardList.append(parsedLine)
                else:
                    pass

        outputList = [header]
        if len(standardList) >= 2:
            for stdId in range(len(standardList)-1):
                outputList.append(colFormat % tuple(standardList[stdId]))
                standardDeltaOffset = (float(standardList[stdId][8]) + float(standardList[stdId+1][8]))/2 - float(standardList[stdId][12])
                standard12CO2Offset = (float(standardList[stdId][9]) + float(standardList[stdId+1][9]))/2 - float(standardList[stdId][13])
                for sampleId in range(len(sampleBagList[stdId])):
                    # Fill in the "Corrected Delta" column
                    sampleBagList[stdId][sampleId][2] = "%15.3f" % (float(sampleBagList[stdId][sampleId][4]) - standardDeltaOffset)
                    sampleBagList[stdId][sampleId][3] = "%15.3f" % (float(sampleBagList[stdId][sampleId][5]) - standard12CO2Offset)
                    outputList.append(colFormat % tuple(sampleBagList[stdId][sampleId]))
            outputList.append(colFormat % tuple(standardList[-1]))        
            fd = open(self.outputFilename, "w")
            fd.writelines(outputList)
            fd.close()
        else:
            print "No enough standard measurement for delta correction"
 
if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = DeltaCorrProcessorFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()