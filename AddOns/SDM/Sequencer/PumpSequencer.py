# PumpSequencer.py
#
# File History:
#    2014-03-31 tw    Extracted from WinXP release

import sys
import os
import wx
import threading
import getopt
from PumpSequencerFrame import PumpSequencerFrame, NUM_OPTS

class PumpSequencer(PumpSequencerFrame):

    def __init__(self, *args, **kwds):
        PumpSequencerFrame.__init__(self, *args, **kwds)
        self.seqData = []
        self.filename = None
        self.defaultPath = None
        self.activeFile = os.getcwd() + '\\active.seq'
        self.bindEvents()
        if os.path.isfile(self.activeFile):
            self.onLoadFileMenu(None, self.activeFile)
        return

    def bindEvents(self):
        self.Bind(wx.EVT_MENU, self.onLoadFileMenu, id=self.idLoadFile)
        self.Bind(wx.EVT_MENU, self.onSaveFileMenu, id=self.idSaveFile)
        self.Bind(wx.EVT_SPINCTRL, self.onTotStepsSpinCtrl, self.spinCtrlTotSteps)
        self.Bind(wx.EVT_BUTTON, self.onEnRotButton, self.buttonEnRot)
        self.Bind(wx.EVT_BUTTON, self.onApplyButton, self.buttonApply)
        self.Bind(wx.EVT_BUTTON, self.onCloseButton, self.buttonClose)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        for idx in range(NUM_OPTS - 2):
            self.Bind(wx.EVT_TEXT, self.onFlowRateTextCtrl, self.flowRateTextCtrlList[idx])

        self.bindDynamicEvents()

    def bindDynamicEvents(self):
        """Dynamic binding that changes as the user modifies the valve sequence.
        """
        for row in range(self.numSteps):
            self.Bind(wx.EVT_TEXT, self.onDurationTextCtrl, self.durationTextCtrlList[row])
            self.Bind(wx.EVT_TEXT, self.onRotValCodeTextCtrl, self.rotValCodeTextCtrlList[row])
            for idx in range(NUM_OPTS):
                self.Bind(wx.EVT_CHECKBOX, self.onOptCheckbox, self.optCheckboxSet[row][idx])

    def onTotStepsSpinCtrl(self, event):
        self._addTitleNote()
        self.setNumSteps(self.spinCtrlTotSteps.GetValue())
        self.setPanelCtrl(loadNewSeq=False)
        self.doLayout()
        self.bindDynamicEvents()

    def onApplyButton(self, event):
        self.seqData = []
        for row in range(self.spinCtrlTotSteps.GetValue()):
            newData = '%10s %10d %10s\n' % (self.durationTextCtrlList[row].GetValue(), self.optPosValue[row], self.rotValCodeTextCtrlList[row].GetValue())
            self.seqData.append(newData)

        flowRateValues = ''
        for idx in range(NUM_OPTS - 2):
            flowRateValues += '%s ' % self.flowRateTextCtrlList[idx].GetValue().strip()

        flowRateValues += '\n'
        self.seqData.append(flowRateValues)
        if self.enRot:
            self.seqData.append('Rotary valve enabled = True')
        else:
            self.seqData.append('Rotary valve enabled = False')
        try:
            fd = open(self.activeFile, 'w')
            fd.writelines(self.seqData)
            fd.close()
            self.SetTitle('Syringe Pump Sequence Setup (%s)' % self.activeFile)
        except Exception as errMsg:
            wx.MessageBox('Saving %s failed!\nPython Error: %s' % (self.activeFile, errMsg))

        dlg = wx.MessageDialog(None, 'Please start or re-start CRDS Coordinator to execute the new sequence.', 'Syringe Pump Sequence Ready', style=wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP)
        dlg.ShowModal()
        dlg.Destroy()
        return

    def onEnRotButton(self, event):
        if not self.enRot:
            for textCtrl in self.rotValCodeTextCtrlList:
                textCtrl.Enable(True)

            self.buttonEnRot.SetLabel('Disable Rotary Valve')
            self.enRot = True
        else:
            for textCtrl in self.rotValCodeTextCtrlList:
                textCtrl.Enable(False)

            self.buttonEnRot.SetLabel('Enable Rotary Valve')
            self.enRot = False

    def onCloseButton(self, event):
        sys.exit()

    def onOptCheckbox(self, event):
        self._addTitleNote()
        row, pos = divmod(self.optIdList.index(event.GetEventObject().GetId()), NUM_OPTS)
        for col in range(NUM_OPTS):
            if col != pos:
                self.optCheckboxSet[row][col].SetValue(0)

        if self.optCheckboxSet[row][pos].GetValue():
            self.optPosValue[row] = pos
        else:
            self.optPosValue[row] = -1

    def onFlowRateTextCtrl(self, event):
        try:
            if float(event.GetEventObject().GetValue()) > 0.08:
                event.GetEventObject().SetValue('0.08')
            if float(event.GetEventObject().GetValue()) < 0.0:
                event.GetEventObject().SetValue('0.0')
        except:
            pass

        self._addTitleNote()

    def onDurationTextCtrl(self, event):
        self._addTitleNote()

    def onRotValCodeTextCtrl(self, event):
        self._addTitleNote()

    def _addTitleNote(self):
        curTitle = self.GetTitle()
        if curTitle != 'Syringe Pump Sequence Setup' and curTitle[-1] != '*':
            self.SetTitle(curTitle + '*')

    def onClose(self, event):
        sys.exit()

    def onLoadFileMenu(self, event, filename = None):
        if not filename:
            if not self.defaultPath:
                self.defaultPath = os.getcwd()
            dlg = wx.FileDialog(self, 'Select Valve Sequence File...', self.defaultPath, wildcard='*.seq', style=wx.OPEN)
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
            fd = open(self.filename, 'r')
            self.seqData = fd.readlines()
            fd.close()
        except Exception as errMsg:
            wx.MessageBox('Loading %s failed!\nPython Error: %s' % (self.filename, errMsg))
            return

        numSteps = len(self.seqData) - 2
        self.spinCtrlTotSteps.SetValue(numSteps)
        self.setNumSteps(numSteps)
        self.setPanelCtrl(loadNewSeq=True)
        self.doLayout()
        self.bindDynamicEvents()
        for row in range(numSteps):
            dur, optPos, rotValCode = self.seqData[row].split()[:3]
            self.durationTextCtrlList[row].SetValue(dur)
            pos = int(optPos)
            if pos != -1:
                for col in range(NUM_OPTS):
                    if col != pos:
                        self.optCheckboxSet[row][col].SetValue(0)
                    else:
                        self.optCheckboxSet[row][col].SetValue(1)

            else:
                for col in range(NUM_OPTS):
                    self.optCheckboxSet[row][col].SetValue(0)

            self.optPosValue[row] = pos
            self.rotValCodeTextCtrlList[row].SetValue(rotValCode)

        flowRateValues = self.seqData[-2].split()
        for idx in range(NUM_OPTS - 2):
            self.flowRateTextCtrlList[idx].SetValue(flowRateValues[idx])

        self.enRot = eval(self.seqData[-1].split('=')[1])
        if self.enRot:
            for textCtrl in self.rotValCodeTextCtrlList:
                textCtrl.Enable(True)

            self.buttonEnRot.SetLabel('Disable Rotary Valve')
        else:
            for textCtrl in self.rotValCodeTextCtrlList:
                textCtrl.Enable(False)

            self.buttonEnRot.SetLabel('Enable Rotary Valve')
        self.SetTitle('Syringe Pump Sequence Setup (%s)' % self.filename)

    def onSaveFileMenu(self, event):
        self.seqData = []
        for row in range(self.spinCtrlTotSteps.GetValue()):
            newData = '%10s %10d %10s\n' % (self.durationTextCtrlList[row].GetValue(), self.optPosValue[row], self.rotValCodeTextCtrlList[row].GetValue())
            self.seqData.append(newData)

        flowRateValues = ''
        for idx in range(NUM_OPTS - 2):
            flowRateValues += '%s   ' % self.flowRateTextCtrlList[idx].GetValue().strip()

        flowRateValues += '\n'
        self.seqData.append(flowRateValues)
        if self.enRot:
            self.seqData.append('Rotary valve enabled = True')
        else:
            self.seqData.append('Rotary valve enabled = False')
        if self.filename:
            defaultPSFile = self.filename
        else:
            defaultPSFile = ''
        if not self.defaultPath:
            self.defaultPath = os.getcwd()
        dlg = wx.FileDialog(self, 'Save Valve Sequence as...', self.defaultPath, defaultPSFile, wildcard='*.seq', style=wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            if not os.path.splitext(filename)[1]:
                filename = filename + '.seq'
            self.filename = filename
            self.defaultPath = os.path.dirname(self.filename)
            try:
                fd = open(self.filename, 'w')
                fd.writelines(self.seqData)
                fd.close()
                self.SetTitle('Syringe Pump Sequence Setup (%s)' % self.filename)
            except Exception as errMsg:
                wx.MessageBox('Saving %s failed!\nPython Error: %s' % (self.filename, errMsg))

        dlg.Destroy()


HELP_STRING = 'PumpSequencer [-h] [--enable_rot]\n\nWhere the options can be a combination of the following:\n-h                  Print this help.\n--enable_rot        Enable rotary valve control on GUI.\n'

def printUsage():
    print HELP_STRING


def handleCommandSwitches():
    shortOpts = 'c:h'
    longOpts = ['help']
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError as data:
        print '%s %r' % (data, data)
        sys.exit(1)

    options = {}
    for o, a in switches:
        options[o] = a

    if '/?' in args or '/h' in args:
        options['-h'] = ''
    if '-h' in options or '--help' in options:
        printUsage()
        sys.exit(0)


if __name__ == '__main__':
    handleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = PumpSequencer(None, -1, '')
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()