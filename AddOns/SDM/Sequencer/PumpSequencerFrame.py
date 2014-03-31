# PumpSequencer.py
#
# File History:
#    2014-03-31 tw    Extracted from WinXP release

import wx
DEFAULT_NUM_STEPS = 10
NUM_OPTS = 8
FORMAT_OPTION = 2

class PumpSequencerFrame(wx.Frame):

    def __init__(self, *args, **kwds):
        self.numSteps = DEFAULT_NUM_STEPS
        self.lastNumSteps = 0
        self.enRot = False
        kwds['style'] = wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = wx.ScrolledWindow(self, -1, style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL | wx.ALWAYS_SHOW_SB)
        self.frameMenubar = wx.MenuBar()
        menuItem = wx.Menu()
        self.idLoadFile = wx.NewId()
        self.idSaveFile = wx.NewId()
        menuItem.Append(self.idLoadFile, 'Load Pump Sequence File', '', wx.ITEM_NORMAL)
        menuItem.Append(self.idSaveFile, 'Save Pump Sequence File', '', wx.ITEM_NORMAL)
        self.frameMenubar.Append(menuItem, 'File')
        self.SetMenuBar(self.frameMenubar)
        self.labelTitle = wx.StaticText(self, -1, 'Syringe Pump Sequence Setup', style=wx.ALIGN_CENTRE)
        self.labelTotSteps = wx.StaticText(self, -1, 'Total Steps', style=wx.ALIGN_CENTRE)
        self.labelBlank = wx.StaticText(self, -1, '', style=wx.ALIGN_CENTRE)
        self.labelFlowRate = wx.StaticText(self, -1, 'Flow Rate (micro-L/s)', style=wx.ALIGN_CENTRE)
        self.labelStep = wx.StaticText(self, -1, 'Step #', style=wx.ALIGN_CENTRE)
        self.labelDuration = wx.StaticText(self, -1, 'Duration (min)', style=wx.ALIGN_CENTRE)
        self.curOptLabelList = []
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump1/Conc1', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump1/Conc2', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump1/Conc3', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump2/Conc1', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump2/Conc2', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Pump2/Conc3', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Vapor1', style=wx.ALIGN_CENTRE))
        self.curOptLabelList.append(wx.StaticText(self, -1, 'Vapor2', style=wx.ALIGN_CENTRE))
        self.labelRotVal = wx.StaticText(self, -1, 'Rot. Valve Code', style=wx.ALIGN_CENTRE)
        self.flowRateTextCtrlList = []
        for idx in range(NUM_OPTS - 2):
            textCtrl = wx.TextCtrl(self, -1, '0.0', style=wx.TE_PROCESS_ENTER | wx.TE_CENTRE)
            textCtrl.SetMinSize((70, 20))
            self.flowRateTextCtrlList.append(textCtrl)

        self.spinCtrlTotSteps = wx.SpinCtrl(self, -1, str(self.numSteps), min=1, max=200, style=wx.TE_PROCESS_ENTER | wx.TE_CENTRE)
        self.buttonEnRot = wx.Button(self, -1, 'Enable Rotary Valve', style=wx.BU_EXACTFIT)
        self.buttonApply = wx.Button(self, -1, 'Apply', style=wx.BU_EXACTFIT)
        self.buttonClose = wx.Button(self, -1, 'Close', style=wx.BU_EXACTFIT)
        self.staticLine = wx.StaticLine(self, -1)
        self.SetTitle('Syringe Pump Sequence Setup')
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.labelTitle.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ''))
        self.panel.SetScrollRate(10, 10)
        self.buttonEnRot.SetMinSize((100, 20))
        self.buttonEnRot.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonEnRot.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ''))
        self.buttonApply.SetMinSize((100, 20))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonApply.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ''))
        self.buttonClose.SetMinSize((100, 20))
        self.buttonClose.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonClose.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ''))
        self.stepTextCtrlList = []
        self.durationTextCtrlList = []
        self.rotValCodeTextCtrlList = []
        self.optIdList = []
        self.durationIdList = []
        self.rotValCodeIdList = []
        self.optPosValue = []
        self.optCheckboxSet = []
        self.setPanelCtrl()
        self.doLayout()

    def setNumSteps(self, numSteps):
        self.lastNumSteps = self.numSteps
        self.numSteps = numSteps

    def setPanelCtrl(self, loadNewSeq = False):
        contTextCtrlList = [self.durationTextCtrlList, self.rotValCodeTextCtrlList]
        curNumRows = len(self.stepTextCtrlList)
        if loadNewSeq and self.numSteps <= curNumRows:
            totTextCtrlList = contTextCtrlList + [self.stepTextCtrlList]
            for row in range(self.numSteps):
                contTextCtrlList[0][row].Enable(True)
                if self.enRot:
                    contTextCtrlList[1][row].Enable(True)
                else:
                    contTextCtrlList[1][row].Enable(False)
                for elemIdx in range(NUM_OPTS):
                    self.optCheckboxSet[row][elemIdx].Enable(True)

            for row in range(self.numSteps, curNumRows):
                for textCtrlList in totTextCtrlList:
                    textCtrlList[row].Destroy()

                for elemIdx in range(NUM_OPTS):
                    self.optCheckboxSet[row][elemIdx].Destroy()

            self.optIdList = self.optIdList[:NUM_OPTS * self.numSteps]
            self.durationIdList = self.durationIdList[:self.numSteps]
            self.rotValCodeIdList = self.rotValCodeIdList[:self.numSteps]
            self.optPosValue = self.optPosValue[:self.numSteps]
            for row in range(self.numSteps, curNumRows):
                for textCtrlList in totTextCtrlList:
                    textCtrlList.remove(textCtrlList[-1])

                self.optCheckboxSet.remove(self.optCheckboxSet[-1])

            return
        if self.numSteps < self.lastNumSteps:
            for row in range(self.numSteps, self.lastNumSteps):
                for textCtrlList in contTextCtrlList:
                    textCtrlList[row].Enable(False)

                for elemIdx in range(NUM_OPTS):
                    self.optCheckboxSet[row][elemIdx].Enable(False)

        elif self.lastNumSteps == self.numSteps:
            pass
        elif self.numSteps <= curNumRows:
            for row in range(self.lastNumSteps, self.numSteps):
                contTextCtrlList[0][row].Enable(True)
                if self.enRot:
                    contTextCtrlList[1][row].Enable(True)
                else:
                    contTextCtrlList[1][row].Enable(False)
                for elemIdx in range(NUM_OPTS):
                    self.optCheckboxSet[row][elemIdx].Enable(True)

        else:
            for row in range(self.lastNumSteps, curNumRows):
                contTextCtrlList[0][row].Enable(True)
                if self.enRot:
                    contTextCtrlList[1][row].Enable(True)
                else:
                    contTextCtrlList[1][row].Enable(False)
                for elemIdx in range(NUM_OPTS):
                    self.optCheckboxSet[row][elemIdx].Enable(True)

            for row in range(self.numSteps - curNumRows):
                textCtrl = wx.TextCtrl(self.panel, -1, str(curNumRows + row + 1), style=wx.TE_READONLY | wx.TE_CENTRE)
                textCtrl.SetMinSize((80, 20))
                textCtrl.SetBackgroundColour(wx.Colour(206, 206, 206))
                self.stepTextCtrlList.append(textCtrl)
                durationId = wx.NewId()
                textCtrl = wx.TextCtrl(self.panel, durationId, '0', style=wx.TE_CENTRE)
                textCtrl.SetMinSize((100, 20))
                self.durationTextCtrlList.append(textCtrl)
                self.durationIdList.append(durationId)
                checkboxList = []
                for idx in range(NUM_OPTS):
                    cbId = wx.NewId()
                    checkbox = wx.CheckBox(self.panel, cbId, '')
                    checkbox.SetMinSize((20, 20))
                    checkboxList.append(checkbox)
                    self.optIdList.append(cbId)

                self.optCheckboxSet.append(checkboxList)
                self.optPosValue.append(-1)
                rotValCodeId = wx.NewId()
                textCtrl = wx.TextCtrl(self.panel, rotValCodeId, '0', style=wx.TE_PROCESS_ENTER | wx.TE_CENTRE)
                textCtrl.SetMinSize((100, 20))
                if self.enRot:
                    textCtrl.Enable(True)
                else:
                    textCtrl.Enable(False)
                self.rotValCodeTextCtrlList.append(textCtrl)
                self.rotValCodeIdList.append(rotValCodeId)

    def doLayout(self):
        sizerToplevel = wx.BoxSizer(wx.VERTICAL)
        sizerMainLayout = wx.BoxSizer(wx.VERTICAL)
        sizerMainLayout.Add(self.labelTitle, 0, wx.BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 30)
        sizerCtrl = wx.BoxSizer(wx.HORIZONTAL)
        sizerTotSteps = wx.BoxSizer(wx.VERTICAL)
        sizerEnRot = wx.BoxSizer(wx.VERTICAL)
        sizerApply = wx.BoxSizer(wx.VERTICAL)
        sizerClose = wx.BoxSizer(wx.VERTICAL)
        sizerTotSteps.Add(self.labelTotSteps, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizerTotSteps.Add(self.spinCtrlTotSteps, 0, wx.ALL | wx.EXPAND, 4)
        sizerCtrl.Add(sizerTotSteps, 1, 0, 0)
        sizerEnRot.Add(self.labelBlank, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizerEnRot.Add(self.buttonEnRot, 0, wx.ALL | wx.EXPAND, 4)
        sizerCtrl.Add(sizerEnRot, 1, 0, 0)
        sizerApply.Add(self.labelBlank, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizerApply.Add(self.buttonApply, 0, wx.ALL | wx.EXPAND, 4)
        sizerCtrl.Add(sizerApply, 1, 0, 0)
        sizerClose.Add(self.labelBlank, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 4)
        sizerClose.Add(self.buttonClose, 0, wx.ALL | wx.EXPAND, 4)
        sizerCtrl.Add(sizerClose, 1, 0, 0)
        if FORMAT_OPTION == 1:
            sizerMainLayout.Add(sizerCtrl, 0, wx.RIGHT | wx.EXPAND, 20)
            sizerMainLayout.Add(self.staticLine, 0, wx.EXPAND, 0)
        sizerDisplayAndPanel = wx.BoxSizer(wx.VERTICAL)
        sizerFlowRate = wx.BoxSizer(wx.HORIZONTAL)
        sizerCurDisplay = wx.BoxSizer(wx.HORIZONTAL)
        sizerCurOptLabels = wx.BoxSizer(wx.HORIZONTAL)
        sizerFlowRate.Add((97, -1))
        sizerFlowRate.Add(self.labelFlowRate, 0, wx.RIGHT, 14)
        for idx in range(NUM_OPTS - 2):
            sizerFlowRate.Add((7.7, -1), proportion=0)
            sizerFlowRate.Add(self.flowRateTextCtrlList[idx], 0)

        sizerCurDisplay.Add(self.labelStep, 0, wx.LEFT | wx.RIGHT, 35)
        sizerCurDisplay.Add(self.labelDuration, 0, wx.LEFT | wx.RIGHT, 5)
        sizerCurOptLabels.Add((10, -1), 0, wx.RIGHT, 5)
        for idx in range(NUM_OPTS):
            if idx in range(NUM_OPTS - 2):
                sizerCurOptLabels.Add((11, -1), proportion=0)
                sizerCurOptLabels.Add(self.curOptLabelList[idx], 0)
            elif idx == NUM_OPTS - 2:
                sizerCurOptLabels.Add((29, -1), proportion=0)
                sizerCurOptLabels.Add(self.curOptLabelList[idx], 0)
            elif idx == NUM_OPTS - 1:
                sizerCurOptLabels.Add((40, -1), proportion=0)
                sizerCurOptLabels.Add(self.curOptLabelList[idx], 0)

        sizerCurDisplay.Add(sizerCurOptLabels, 0, wx.LEFT | wx.RIGHT, 15)
        sizerCurDisplay.Add(self.labelRotVal, 0, wx.LEFT | wx.RIGHT, 30)
        sizerDisplayAndPanel.Add(sizerFlowRate, 1, wx.RIGHT | wx.EXPAND, 20)
        sizerDisplayAndPanel.Add((-1, 10))
        sizerDisplayAndPanel.Add(sizerCurDisplay, 1, wx.RIGHT | wx.EXPAND, 20)
        sizerPanel = wx.BoxSizer(wx.VERTICAL)
        for row in range(self.numSteps):
            sizerPanelColumn = wx.BoxSizer(wx.HORIZONTAL)
            sizerChecklist = wx.BoxSizer(wx.HORIZONTAL)
            sizerPanelColumn.Add(self.stepTextCtrlList[row], 0, wx.ALL | wx.EXPAND, 4)
            sizerPanelColumn.Add(self.durationTextCtrlList[row], 0, wx.ALL | wx.EXPAND, 4)
            checkboxList = self.optCheckboxSet[row]
            sizerChecklist.Add((50, -1), 0)
            for idx in range(NUM_OPTS):
                sizerChecklist.Add(checkboxList[idx], 0, wx.TOP | wx.BOTTOM, 4)
                if idx != NUM_OPTS - 1:
                    sizerChecklist.Add((57, -1), 0)

            sizerChecklist.Add((35, -1), 0)
            sizerPanelColumn.Add(sizerChecklist, 0, wx.EXPAND, wx.LEFT, 4)
            sizerPanelColumn.Add(self.rotValCodeTextCtrlList[row], 0, wx.ALL | wx.EXPAND, 4)
            sizerPanel.Add(sizerPanelColumn, 0, wx.EXPAND, 0)

        self.panel.SetSizer(sizerPanel)
        sizerDisplayAndPanel.Add(self.panel, 24, wx.EXPAND, 0)
        sizerMainLayout.Add(sizerDisplayAndPanel, 0, wx.BOTTOM, 5)
        if FORMAT_OPTION == 2:
            sizerMainLayout.Add(self.staticLine, 0, wx.EXPAND, 0)
            sizerMainLayout.Add(sizerCtrl, 0, wx.EXPAND, 0)
        sizerToplevel.Add(sizerMainLayout, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 30)
        self.SetSizer(sizerToplevel)
        sizerToplevel.Fit(self)
        sizerPanel.FitInside(self.panel)
        self.Layout()