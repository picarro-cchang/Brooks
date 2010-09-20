#!/usr/bin/python
#
# File Name: DataRecal.py
# Purpose: Delta value re-calibration for Iso systems
#
# File History:
# 09-08-28 alex  Created

import sys
import os
import stat
import wx
import getopt
import time
from numpy import *
from matplotlib import pyplot
from matplotlib.artist import *
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DATA_MANAGER
from DataRecalFrame import DataRecalFrame
DATA_MANAGER = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DATA_MANAGER, ClientName = "DataRecal")

class DataRecal(DataRecalFrame):
    def __init__(self, calIniFile, *args, **kwds):
        cp = CustomConfigObj(calIniFile, list_values = True)
        try:
            dataList = cp.list_sections()
        except:
            dataList = []
        DataRecalFrame.__init__(self, dataList, *args, **kwds)
        self.panel1.SetBackgroundColour("#C3FDB8")
        self.panel2.SetBackgroundColour("#64E986")
        self.panel3.SetBackgroundColour("#85B24A")
        
        self.dataType = dataList[0]
        self.cfgData = []
        self._showUpdatedCurCal()
        self.newOffset = None
        self.newSlope = None
        self.r2 = None
        self.filename = None
        self.defaultPath = None
        self.activeFile = os.getcwd()+"\\active.cfg"
        self.bindEvents()
        if self._getNumSelectedRows() == 0:
            self.buttonCompute.Enable(False)
        self.buttonApply.Enable(False)
        self.iPlotFit.Enable(False)
        
    def bindEvents(self):       
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, self.iLoadFile)
        self.Bind(wx.EVT_MENU, self.onPlotFitMenu, self.iPlotFit)
        self.Bind(wx.EVT_COMBOBOX, self.onOptionComboBox, self.optionComboBox)
        self.Bind(wx.EVT_COMBOBOX, self.onDataComboBox, self.dataComboBox)
        self.Bind(wx.EVT_BUTTON, self.onComputeButton, self.buttonCompute)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply)    
        self.Bind(wx.EVT_BUTTON, self.onClearButton, self.buttonClear)
        self.Bind(wx.EVT_BUTTON, self.onExitButton, self.buttonExit)           
        self.Bind(wx.EVT_CLOSE, self.onClose)
        for row in range(self.numRows):
            self.Bind(wx.EVT_CHECKBOX, self.onCheckbox, self.checkboxList[row])
            self.Bind(wx.EVT_TEXT, self.onAcceptTextCtrl, self.acceptTextCtrlList[row])
            self.Bind(wx.EVT_TEXT, self.onReportTextCtrl, self.reportTextCtrlList[row])
            
    def onComputeButton(self, event):
        accDataList = []
        repDataList = []
        for row in range(self.numRows):
            if self.checkboxList[row].GetValue():
                try:
                    accDataList.append(float(self.acceptTextCtrlList[row].GetValue()))
                    repDataList.append(float(self.reportTextCtrlList[row].GetValue()))
                except:
                    d = wx.MessageDialog(None, "Invalid value entered.", "Invalid Value", wx.OK|wx.ICON_ERROR)
                    d.ShowModal()
                    d.Destroy()
                    return
        accAry = array(accDataList)
        repAry = array(repDataList)
        if len(repAry) < 1:
            d = wx.MessageDialog(None, "Recal data not selected, action cancelled.", "Error", wx.OK|wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return

        recalDataList = []
        if self.optionComboBox.GetValue() == " Offset Only":
            aveOffsetShift = mean(accAry-repAry)
            self.newOffset = self.curOffset + aveOffsetShift
            self.newSlope = self.curSlope
            # Update recalibrated values
            for row in range(self.numRows):
                recalValue = float(self.reportTextCtrlList[row].GetValue())+aveOffsetShift
                self.recalTextCtrlList[row].SetValue("%.5f" % recalValue)
                if self.checkboxList[row].GetValue():
                    recalDataList.append(recalValue)
        else:
            if len(repAry) < 2:
                d = wx.MessageDialog(None, "'Offset + Slope' option requires at least 2 recal data points, action cancelled.", "Error", wx.OK|wx.ICON_ERROR)
                d.ShowModal()
                d.Destroy()
                return
            (m, b) = polyfit(repAry, accAry, 1)
            self.newOffset = m*self.curOffset+b
            self.newSlope = m*self.curSlope
            # Update recalibrated values
            for row in range(self.numRows):
                recalValue = m*float(self.reportTextCtrlList[row].GetValue())+b
                self.recalTextCtrlList[row].SetValue("%.5f" % recalValue)
                if self.checkboxList[row].GetValue():
                    recalDataList.append(recalValue)
        # Calculate R2
        recAry = array(recalDataList)
        resSq = sum((accAry - recAry)**2)
        accSq = sum((accAry - mean(accAry))**2)
        if accSq != 0.0:
            self.r2 = 1 - (resSq/accSq)
        else:
            self.r2 = "invalid"
        if self.r2 != "invalid":
            self.r2TextCtrl.SetValue("%.5f" % self.r2)
        else:
            self.r2TextCtrl.SetValue("NA")
        self.newOffsetTextCtrl.SetValue("%.5f" % self.newOffset)
        self.newSlopeTextCtrl.SetValue("%.5f" % self.newSlope)
        if abs(self.newSlope) < 1e-10:
            d = wx.MessageDialog(None, "New slope value (=0) not acceptable. Please change calibration setup and try again.", "Invalid new slope value", wx.OK|wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return
    
        curTitle = self.GetTitle()
        if curTitle.endswith("*"):
            self.SetTitle(curTitle[:-1])
        self.buttonCompute.Enable(False)
        self.buttonApply.Enable(True)
        self.iPlotFit.Enable(True)

    def onApplyButton(self, event):
        # Use password to protect user cal function
        d = wx.TextEntryDialog(self, 'Please ensure you want to change the calibration factors.\n\nTHIS ACTION CANNOT BE UNDONE.\n\nUser Calibration Password: ','Authorization required', '', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
        password = "picarro"
        okClicked = d.ShowModal() == wx.ID_OK
        d.Destroy()
        if not okClicked:
            return
        elif d.GetValue() != password:
            d = wx.MessageDialog(None, "Password incorrect, action cancelled.", "Incorrect Password", wx.OK|wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return
        
        d = wx.MessageDialog(None, "Data = %s\nNew offset = %.5f\nNew slope  = %.5f\n\nAre you sure you want to change?"%(self.dataType, self.newOffset, self.newSlope), \
                            "Recalibration Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
        if d.ShowModal() != wx.ID_YES:
            d.Destroy()
            return
        else:
            d.Destroy()
        
        # Ask Data Manager to update user calibration
        DATA_MANAGER.Cal_SetSlopeAndOffset(self.dataType, self.newSlope, self.newOffset)
            
        # Save sequence to the "active" file
        self.cfgData = []
        self.cfgData.append("%10s %10s\n" % ("data",self.dataType))
        for row in range(self.numRows):
            if self.checkboxList[row].GetValue():
                newData = "%10s %10s %10s\n" % (self.acceptTextCtrlList[row].GetValue(),
                                                self.reportTextCtrlList[row].GetValue(),
                                                self.recalTextCtrlList[row].GetValue())
                self.cfgData.append(newData)
        newData = "%10s %10s %10s\n" % ("cc",
                                        self.curOffsetTextCtrl.GetValue(),
                                        self.curSlopeTextCtrl.GetValue())
        self.cfgData.append(newData)
        newData = "%10s %10s %10s %10s\n" % ("nc",
                                        self.newOffsetTextCtrl.GetValue(),
                                        self.newSlopeTextCtrl.GetValue(),
                                        self.r2TextCtrl.GetValue())
        self.cfgData.append(newData)
        self.cfgData.append("%10s %10s\n" % ("option", self.optionComboBox.GetValue()))
        
        try:
            fd = open(self.activeFile, "w")
            fd.writelines(self.cfgData)
            fd.close()
        except Exception, errMsg:
            wx.MessageBox("Saving %s failed!\nPython Error: %s" % (self.activeFile, errMsg))
        
        d = wx.MessageDialog(None,"Recalibration done", "Calibration Updated", wx.ICON_INFORMATION | wx.STAY_ON_TOP)
        d.ShowModal()
        d.Destroy()

        # Ask user to save a copy too
        try:
            self.onSaveFileMenu(None)
            self._showUpdatedCurCal()
            self.buttonApply.Enable(False)
            self.SetTitle("Picarro Data Recalibration (%s)" % os.path.basename(self.filename))
        except:
            pass
    
    def onClearButton(self, event):
        d = wx.MessageDialog(None, "Are you sure you want to clear all the entries?\nCurrent calibration will not be affected.\n\nSelect \"Yes\" to continue.\nSelect \"No\" to cancel this action.",\
                        "Clear Entries Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
        if d.ShowModal() != wx.ID_YES:
            d.Destroy()
            return
        else:
            d.Destroy()
        for row in range(self.numRows):
            self.acceptTextCtrlList[row].SetValue("0.00000")
            self.reportTextCtrlList[row].SetValue("0.00000")      
            self.recalTextCtrlList[row].SetValue("0.00000")  
            self.checkboxList[row].SetValue(False) 
        self.newOffsetTextCtrl.SetValue("0.00000")
        self.newSlopeTextCtrl.SetValue("0.00000")
        self.r2TextCtrl.SetValue("0.00000")
        
    def onExitButton(self, event):
        if self.buttonApply.IsEnabled():
            d = wx.MessageDialog(None, "New calibration not applied yet. Are you sure you want to exit now?\nTo apply the new calibration please click \"Apply New Cal\" button before exiting.\n\nSelect \"Yes\" to exit without saving the new calibration.\nSelect \"No\" to cancel this action.",\
                            "Exit Confirmation", wx.YES_NO|wx.ICON_EXCLAMATION)
            if d.ShowModal() != wx.ID_YES:
                d.Destroy()
                return
            else:
                d.Destroy()
        self.Destroy()

    def onOptionComboBox(self, event):
        self._onAnyChange()
        
    def onDataComboBox(self, event):
        self._onAnyChange()
        
    def onCheckbox(self, event):
        self._onAnyChange()

    def onAcceptTextCtrl(self, event):
        self._onAnyChange()
            
    def onReportTextCtrl(self, event):
        self._onAnyChange()

    def _onAnyChange(self):
        self.dataType = self.dataComboBox.GetValue().strip()
        self.buttonApply.Enable(False)
        curTitle = self.GetTitle()
        if not curTitle.endswith("*"):
            self.SetTitle(curTitle + "*")

        numSelRows = self._getNumSelectedRows()
        if numSelRows == 0:
            self.buttonCompute.Enable(False)
        elif numSelRows == 1 and self.optionComboBox.GetValue() == " Offset + Slope":
            self.buttonCompute.Enable(False)
        else:
            self.buttonCompute.Enable(True)
        self._showUpdatedCurCal()
        
    def _enableAll(self, enable):
        for row in range(self.numRows):
            self.acceptTextCtrlList[row].Enable(enable)
            self.reportTextCtrlList[row].Enable(enable)    
            self.checkboxList[row].Enable(enable)
        
    def _getNumSelectedRows(self):
        numSelRows = 0
        for row in range(self.numRows):
            if self.checkboxList[row].GetValue():
                numSelRows += 1
        return numSelRows

    def _showUpdatedCurCal(self):
        (self.curSlope, self.curOffset) = DATA_MANAGER.Cal_GetUserCal(self.dataType)
        self.curOffsetTextCtrl.SetValue("%.5f" % self.curOffset)
        self.curSlopeTextCtrl.SetValue("%.5f" % self.curSlope)
        
    def onClose(self, event):
        sys.exit()

    def onPlotFitMenu(self, event):
        repValuePlotList = []
        accValuePlotList = []
        recalValuePlotList = []
        for row in range(self.numRows):
            if (float(self.reportTextCtrlList[row].GetValue()) != 0.0) or (float(self.acceptTextCtrlList[row].GetValue()) != 0.0) or self.checkboxList[row].GetValue():
                accValuePlotList.append(float(self.acceptTextCtrlList[row].GetValue()))
                repValuePlotList.append(float(self.reportTextCtrlList[row].GetValue()))
                recalValuePlotList.append(float(self.recalTextCtrlList[row].GetValue()))
        
        if len(repValuePlotList) > 0:
            repPlotAry = array(repValuePlotList)
            order = repPlotAry.argsort()
            repPlotAry = repPlotAry.take(order)
            accPlotAry = array(accValuePlotList)
            accPlotAry = accPlotAry.take(order)
            recalPlotAry = array(recalValuePlotList)
            recalPlotAry = recalPlotAry.take(order)
            resPlotAry = accPlotAry - recalPlotAry

            fig = pyplot.figure()
            fig.subplots_adjust(hspace = 0.35, hspace = 0.35)
            sp1 = fig.add_subplot(2,1,1)
            if self.r2 != "invalid":
                sp1.set_title("Linear fitting (Offset = %.5f, Slope = %.5f, R2 = %.5f)" % (self.newOffset, self.newSlope, self.r2))
            else:
                sp1.set_title("Linear fitting (Offset = %.5f, Slope = %.5f, R2 = N/A)" % (self.newOffset, self.newSlope))
            sp1.grid()
            line1 = sp1.plot(repPlotAry, accPlotAry,'x') 
            line2 = sp1.plot(repPlotAry, recalPlotAry,'-')
            setp(line1, linewidth=1, markeredgewidth=2, markersize=10)
            setp(line2, linewidth=1, markeredgewidth=2, markersize=10)
            sp1.legend([line2],["Calibration Fit"],"best")
            sp1.set_xlabel("Reported Value")
            sp1.set_ylabel("Certified Value")
            sp1.set_xlim((repPlotAry[0]-1, repPlotAry[-1]+1))
            ymax = max(max(accPlotAry),max(recalPlotAry))
            ymin = min(min(accPlotAry),min(recalPlotAry))
            sp1.set_ylim((ymin-1, ymax+1))
    
            sp2 = fig.add_subplot(2,1,2)
            #sp2.set_title("Residual")
            sp2.grid()
            bars = sp2.vlines(repPlotAry, zeros(len(resPlotAry)), resPlotAry, color = "red")
            setp(bars, linewidth=5)
            sp2.plot(repPlotAry, zeros(len(repPlotAry)),'-')
            sp2.set_xlabel("Reported Value")
            sp2.set_ylabel("Residual (Certified-Calibrated)")
            sp2.set_xlim((repPlotAry[0]-1, repPlotAry[-1]+1))
            pyplot.show()
        
    def onLoadFileMenu(self, event, filename = None, disableControls = True):
        if not filename:
            if not self.defaultPath:
                self.defaultPath = os.getcwd()
            dlg = wx.FileDialog(self, "Select IsoCO2 Delta Recalibration Configuration File...",
                                self.defaultPath, wildcard = "*.cfg", style=wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                self.filename = dlg.GetPath()
                dlg.Destroy()
            else:
                dlg.Destroy()
                return
        else:
            self.filename = filename
            
        self.defaultPath = os.path.dirname(self.filename)
        try:
            fd = open(self.filename, "r")
            self.cfgData = fd.readlines()
            fd.close()                
        except Exception, errMsg:
            wx.MessageBox("Loading %s failed!\nPython Error: %s" % (self.filename, errMsg))
            return

        # Clean the whole panel first
        for row in range(self.numRows):
            self.checkboxList[row].SetValue(0)
            self.acceptTextCtrlList[row].SetValue("0.00000")
            self.reportTextCtrlList[row].SetValue("0.00000")
            self.recalTextCtrlList[row].SetValue("0.00000")
            
        # Process the data in the .cfg file
        row = 0
        for line in self.cfgData:
            # Separate the values 
            try:
                parsedLine = line.split()
                if parsedLine[0] == "cc":
                    pass
                    # Current cal values
                    #self.curOffsetTextCtrl.SetValue(parsedLine[1])
                    #self.curSlopeTextCtrl.SetValue(parsedLine[2])
                elif parsedLine[0] == "nc":
                    pass
                    # New cal values
                    #self.newOffsetTextCtrl.SetValue(parsedLine[1])
                    #self.newSlopeTextCtrl.SetValue(parsedLine[2])
                    #self.r2TextCtrl.SetValue(parsedLine[3])
                elif parsedLine[0] == "data":
                    # data type
                    self.dataComboBox.SetValue(parsedLine[1])
                elif parsedLine[0] == "option":
                    # cal option
                    if parsedLine[2] == "Only":
                        self.optionComboBox.SetValue(" Offset Only")
                    else:
                        self.optionComboBox.SetValue(" Offset + Slope")
                else:
                    (accData, repData, recData) = parsedLine
                    self.checkboxList[row].SetValue(1)
                    self.acceptTextCtrlList[row].SetValue(accData)
                    self.reportTextCtrlList[row].SetValue(repData)
                    self.recalTextCtrlList[row].SetValue(recData)
                    row += 1
            except Exception, err:
                print err
                continue
        self.SetTitle("IsoCO2 Delta Recalibration (%s)" % os.path.basename(self.filename))
        if not disableControls:
            self._onAnyChange()
        else:
            self.buttonApply.Enable(False)
            self.buttonCompute.Enable(False)
        
    def onSaveFileMenu(self, event):
        if not self.defaultPath:
            self.defaultPath = os.getcwd()
            
        dlg = wx.FileDialog(self, "Save IsoCO2 Delta Recalibration Configuration as...",
                            self.defaultPath, self._makeFilename(), wildcard = "*.cfg", style=wx.SAVE|wx.OVERWRITE_PROMPT)
                            
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not os.path.splitext(filename)[1]:
                # Ensure filename extension
                filename = filename + ".cfg"
            self.filename = filename
            self.defaultPath = os.path.dirname(self.filename)            
            try:
                fd = open(self.filename, "w")
                fd.writelines(self.cfgData)
                fd.close()
            except Exception, errMsg:
                wx.MessageBox("Saving %s failed!\nPython Error: %s" % (self.filename, errMsg))
        dlg.Destroy()    

    def _makeFilename(self):
        baseFname = "UserRecal"
        return time.strftime(baseFname+"_%Y%m%d_%H%M%S.cfg",time.localtime())
        
        
HELP_STRING = \
"""\
DataRecal [-h] [-c <PicarroCRDS.ini path>]

Where the options can be a combination of the following:
-h                  Print this help.
-c                  Specify the path of PicarroCRDS.ini.
"""
def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'c:h'
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit(0)

    #Start with option defaults...
    calIniFile = "C:\Picarro\G2000\InstrConfig\Calibration\InstrCal\UserCal.ini"
    if "-c" in options:
        calIniFile = options["-c"]
    
    if not os.path.isfile(calIniFile):
        app = wx.App()
        app.MainLoop()
        dlg = wx.FileDialog(None, "Select Data Recalibration .INI file.",
                            os.getcwd(), wildcard = "*.ini", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            calIniFile = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            
    if not os.path.isfile(calIniFile):
        print "\nERROR: Valid Data Recalibration .INI file path must be specified!\n"
        print HELP_STRING
        sys.exit(0)
    else:
        print "Data Recalibration .INI file specified: %s" % calIniFile
        return calIniFile

if __name__ == "__main__":
    calIniFile = handleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = DataRecal(calIniFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
