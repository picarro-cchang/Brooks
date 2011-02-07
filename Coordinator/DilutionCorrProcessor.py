"""
File name: DilutionCorrProcessor.py
Purpose: Post-process output data from dilution system
"""

import os
import sys
import getopt
import wx
from numpy import *

COLUMN_FORMAT = "%15s,"*35+"%15s\n"

class DilutionCorrProcessorFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.STAY_ON_TOP|wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.SetTitle("Dilution Sample Correction")
        self.SetMinSize((270,100))
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.labelFooter = wx.StaticText(self.panel1, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)
        
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
        self.iAbout = wx.MenuItem(self.iHelp, self.idAbout, "About Sample Concentration Correction", "", wx.ITEM_NORMAL)
        self.iHelp.AppendItem(self.iAbout)
        self.SetMenuBar(self.frameMenubar)

        self.textCtrl = wx.TextCtrl(self.panel1, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH)
        self.textCtrl.SetMinSize((250, 80))        

        self.applyButton = wx.Button(self.panel1, -1, "Apply Correction", size=(115,20))
        self.closeButton = wx.Button(self.panel1, wx.ID_CLOSE, "", size=(115,20))
        self.applyButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.closeButton.SetBackgroundColour(wx.Colour(237, 228, 199))
        
        self.comboBoxSelect = wx.ComboBox(self.panel1, -1, choices = ["CO2", "CH4"], value="CO2", style = wx.CB_READONLY|wx.CB_DROPDOWN)
        
        self.__do_layout()
        self.bindEvents()
        self.defaultPath = os.getcwd()
        self.defaultOutPath = os.getcwd()
        self.outputDir = ""
        self.dilType = ""
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
        self.Bind(wx.EVT_COMBOBOX, self.onSelect, self.comboBoxSelect)
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrl)
    
    def onSelect(self, event):
        self.dilType = self.comboBoxSelect.GetValue()
        self.updateTextCtrl()
        
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
        if not self.dilType:
            dlg = wx.MessageDialog(None,"Please select dilution type    ", "Error", style=wx.ICON_EXCLAMATION|wx.STAY_ON_TOP|wx.OK)
            confirm = (dlg.ShowModal() == wx.ID_OK)
            if confirm:
                dlg.Destroy()
                return
        proc = DilutionCorrProcessor(self.dilType, self.outputDir)
        proc.setFilename(self.filename)
        proc.procData()
        if os.path.isfile(proc.getoOutputFilename()):
            self.textCtrl.SetValue("Output file:\nfile:%s\n" % proc.getoOutputFilename())
        else:
            self.textCtrl.SetValue("Failed to create output file")
            
    def onAboutMenu(self, evt):
        d = wx.MessageDialog(None, "This application applies standard concentration to correct sample concentration values.\n\nCopyright 1999-2011 Picarro Inc. All rights reserved.\nVersion: 0.01\nThe copyright of this computer program belongs to Picarro Inc.\nAny reproduction or distribution of this program requires permission from Picarro Inc.", "About Discrete Sample Delta Correction", wx.OK)
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
        msg3 = "3. Select dilution type (CO2 or CH4)"
        if self.filename:
            msg1 += ("\n= %s" % (self.filename))
        if self.outputDir:
            msg2 += ("\n= %s" % (self.outputDir))
        if self.dilType:
            msg3 += ("\n= %s" % (self.dilType))

        self.textCtrl.SetValue("Before applying correction, please:\n%s\n%s\n%s"% (msg1, msg2, msg3))
        if self.filename and self.outputDir and self.dilType:
            self.applyButton.Enable(True)
    
    def __do_layout(self):
        grid_sizer_1 = wx.FlexGridSizer(-1, 3)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1.Add(self.comboBoxSelect, 0, wx.ALL, 5)
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
        
class DilutionCorrProcessor():
    def __init__(self, dilType="CO2", dirname=""):
        self.outputDir = dirname
        self.filepath = ""
        self.outputFilename = ""
        self.dilType = dilType
    
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

        sampleBlock = []
        standardBlock = []
        sampleBlockList = []
        standardBlockList = []
        standardList = []
        lastSource = "Unknown"
        for line in measData:
            parsedLine = line.split(",")
            if len(parsedLine) != 36:
                continue
            for idx in range(len(parsedLine)):
                parsedLine[idx] = parsedLine[idx].strip()
            source = parsedLine[0]
            quality = parsedLine[1]
            if quality == "Good":
                if source.startswith("Sample"):
                    sampleBlock.append(parsedLine)
                    if lastSource == "Standard" and len(standardBlock)>0:
                        standardBlockList.append(standardBlock)
                        standardBlock = []  
                else:
                    standardBlock.append(parsedLine)
                    if lastSource.startswith("Sample") and len(sampleBlock)>0:
                        sampleBlockList.append(sampleBlock)
                        sampleBlock = []
                lastSource = parsedLine[0]
            else:
                pass
        if len(standardBlock)>0:
            standardBlockList.append(standardBlock)
        if len(sampleBlock)>0:
            sampleBlockList.append(sampleBlock)
            
        outputList = [COLUMN_FORMAT[:-1] % tuple(header.split(","))]
        if len(standardBlockList) >= 1:
            # Repeat the first block of standard data without using it
            for std in standardBlockList[0]:
                outputList.append(COLUMN_FORMAT % tuple(std))
            for stdBlockId in range(1, len(standardBlockList)):
                stdSum = 0.0
                for std in standardBlockList[stdBlockId]:
                    if self.dilType.upper() == "CO2":
                        stdSum += float(std[3])
                    else:
                        stdSum += float(std[4])
                stdMean = stdSum/len(standardBlockList[stdBlockId])
                stdConcRatio = stdMean/float(standardBlockList[stdBlockId][0][-1])

                for sampleId in range(len(sampleBlockList[stdBlockId-1])):
                    # Fill in the "Corrected Delta" column
                    if self.dilType.upper() == "CO2":
                        sampleBlockList[stdBlockId-1][sampleId][2] = "%15.3f" % (float(sampleBlockList[stdBlockId-1][sampleId][3])/stdConcRatio)
                    else:
                        sampleBlockList[stdBlockId-1][sampleId][2] = "%15.3f" % (float(sampleBlockList[stdBlockId-1][sampleId][4])/stdConcRatio)
                    outputList.append(COLUMN_FORMAT % tuple(sampleBlockList[stdBlockId-1][sampleId]))
                
                for stdId in range(len(standardBlockList[stdBlockId])):
                    # Fill in the "Corrected Delta" column
                    if self.dilType.upper() == "CO2":
                        standardBlockList[stdBlockId][stdId][2] = "%15.3f" % (float(standardBlockList[stdBlockId][stdId][3])/stdConcRatio)
                    else:
                        standardBlockList[stdBlockId][stdId][2] = "%15.3f" % (float(standardBlockList[stdBlockId][stdId][4])/stdConcRatio)
                    outputList.append(COLUMN_FORMAT % tuple(standardBlockList[stdBlockId][stdId]))       
            
            fd = open(self.outputFilename, "w")
            fd.writelines(outputList)
            fd.close()
        else:
            print "No enough standard measurement for dilution correction"
 
if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = DilutionCorrProcessorFrame(None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()