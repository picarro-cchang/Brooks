# -*- coding: iso-8859-15 -*-
import wx
from wx.lib.masked import TimeCtrl
from datetime import datetime

DEFAULT_NUM_STEPS = 10
FORMAT_OPTION = 2

class ValveSequencerFrame(wx.Frame):
    def __init__(self, numSolValves, numMaxSteps, *args, **kwds):
        self.numSolValves = numSolValves
        self.numSteps = DEFAULT_NUM_STEPS 
        self.lastNumSteps = 0
        
        #kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        kwds["style"] = wx.CAPTION|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = wx.ScrolledWindow(self, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        menuItem = wx.Menu()
        self.idLoadFile = wx.NewId()
        self.idSaveFile = wx.NewId()        
        self.idEnableSeq = wx.NewId()
        #self.idDisableSeq = wx.NewId()
        self.idGoFirstStep = wx.NewId() 
        self.idResetAllValves = wx.NewId()
        self.idHideInterface = wx.NewId()
        
        menuItem.Append(self.idLoadFile, "Load Valve Sequence File", "", wx.ITEM_NORMAL)
        menuItem.Append(self.idSaveFile, "Save Valve Sequence File", "", wx.ITEM_NORMAL)
        self.frameMenubar.Append(menuItem, "File")
        menuItem = wx.Menu()
        menuItem.Append(self.idEnableSeq, "Start Sequencer", "", wx.ITEM_NORMAL)
        #menuItem.Append(self.idDisableSeq, "Disable Sequencer", "", wx.ITEM_NORMAL)
        menuItem.Append(self.idGoFirstStep, "Go To First Step", "", wx.ITEM_NORMAL) 
        menuItem.Append(self.idResetAllValves, "Reset All Valves", "", wx.ITEM_NORMAL)  
        menuItem.Append(self.idHideInterface, "Hide Sequencer Interface", "", wx.ITEM_NORMAL)  
        self.frameMenubar.Append(menuItem, "Action")
        self.SetMenuBar(self.frameMenubar)
        
        # Labels
        self.labelTitle = wx.StaticText(self, -1, "External Valve Sequencer", style=wx.ALIGN_CENTRE)
        self.labelTotSteps = wx.StaticText(self, -1, "Total Steps", size = (150,-1), style=wx.ALIGN_CENTRE)
        self.labelGoToStep = wx.StaticText(self, -1, "Run Step #", size = (150,-1), style=wx.ALIGN_CENTRE)
        self.labelCurStep = wx.StaticText(self, -1, "Current Step #", style=wx.ALIGN_CENTRE)
        self.labelStep = wx.StaticText(self, -1, "Step #", style=wx.ALIGN_CENTRE)        
        self.labelCurDuration = wx.StaticText(self, -1, "Remaining Time (min)", style=wx.ALIGN_CENTRE)
        self.labelDuration = wx.StaticText(self, -1, "Duration (min)", style=wx.ALIGN_CENTRE)
        self.labelCurValState = wx.StaticText(self, -1, "Current Valve State", style=wx.ALIGN_CENTRE)
        self.labelValState = wx.StaticText(self, -1, "Valve State", style=wx.ALIGN_CENTRE)
        self.labelCurValCode = wx.StaticText(self, -1, "Current Valve Code", style=wx.ALIGN_CENTRE)
        self.labelValCode = wx.StaticText(self, -1, "Valve Code", style=wx.ALIGN_CENTRE)
        self.labelCurRotVal = wx.StaticText(self, -1, "Current Rot. Valve Code", style=wx.ALIGN_CENTRE)
        self.labelRotVal = wx.StaticText(self, -1, "Rot. Valve Code", style=wx.ALIGN_CENTRE)
        
        # SpinCtrl for defining "total steps" and "go to step"
        self.spinCtrlTotSteps = wx.SpinCtrl(self, -1, str(self.numSteps), min=1, max=numMaxSteps, style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)        
        self.spinCtrlGoToStep = wx.SpinCtrl(self, -1, "1", min=1, max=numMaxSteps, style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)

        # Buttons
        self.buttonApply = wx.Button(self, -1, "Apply", size = (150,-1))        
        self.buttonRunNext = wx.Button(self, -1, "Run Next Step", size = (150,-1))
        self.buttonSch = wx.Button(self, -1, "Scheduled Sequence", size = (150,-1))

        # Current status display textCtrl
        self.curTextCtrlList = []        
        self.curCheckboxList = []
        textCtrl = wx.TextCtrl(self, -1, "1", style=wx.TE_READONLY|wx.TE_CENTRE)
        textCtrl.SetMinSize((80, 20))
        textCtrl.SetBackgroundColour("#85B24A")
        self.curTextCtrlList.append(textCtrl)
        for idx in range(3):
            textCtrl = wx.TextCtrl(self, -1, "0", style=wx.TE_READONLY|wx.TE_CENTRE)
            textCtrl.SetMinSize((100, 20))
            textCtrl.SetBackgroundColour("#85B24A")
            self.curTextCtrlList.append(textCtrl)
        
        self.curValStateIdList = []    
        for idx in range(self.numSolValves):
            cbId = wx.NewId()
            checkbox = wx.CheckBox(self, cbId, "")
            checkbox.SetMinSize((20, 20))
            checkbox.SetBackgroundColour("#85B24A")
            self.curCheckboxList.append(checkbox)
            self.curValStateIdList.append(cbId)
            
        # Create a small panel to fill the space with color in front of the first checkbox    
        self.checkboxColorFiller = wx.Panel(self, -1)
        self.checkboxColorFiller.SetMinSize((6, 20))
        self.checkboxColorFiller.SetBackgroundColour("#85B24A")
        
        # Divider line
        self.staticLine1 = wx.StaticLine(self, -1)
        self.staticLine2 = wx.StaticLine(self, -1, size=(-1,3))
        
        # Date/time function
        self.labelStartDate = wx.StaticText(self, -1, "Start Date", size = (150,-1), style=wx.ALIGN_CENTRE)
        self.labelStartTime = wx.StaticText(self, -1, "Start Time", size = (150,-1), style=wx.ALIGN_CENTRE)
        self.ctrlStartDate = wx.DatePickerCtrl(self, -1, size = (150,24), style = wx.DP_DROPDOWN)
        self.spinButtonStartTime = wx.SpinButton(self, -1, size=(17,25), style=wx.SP_VERTICAL)
        self.ctrlStartTime = TimeCtrl(self, -1, size = (250,30), fmt24hr=True, spinButton=self.spinButtonStartTime)
        
        # Overall properties
        self.SetTitle("External Valve Sequencer")
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.labelTitle.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.panel.SetScrollRate(10, 10)
        
        # Button properties                    
        self.buttonRunNext.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonRunNext.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonApply.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonSch.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonSch.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

        # Lists reserved for panel control elements
        self.stepTextCtrlList = []
        self.durationTextCtrlList = []
        self.valCodeTextCtrlList = []
        self.rotValCodeTextCtrlList = []
        
        self.valStateIdList = []
        self.durationIdList = []
        self.valCodeIdList = []
        self.rotValCodeIdList = []
        
        self.valStateCheckboxSet = []
        
        # Create the initial frame
        self.spinCtrlGoToStep.SetRange(1, self.numSteps) 
        self.setPanelCtrl()
        self.doLayout()
        
    def setNumSteps(self, numSteps):
        self.lastNumSteps = self.numSteps
        self.numSteps = numSteps   
        self.spinCtrlGoToStep.SetRange(1, numSteps)        

    def setPanelCtrl(self, loadNewSeq = False):                           
        contTextCtrlList = [self.durationTextCtrlList,
                            self.valCodeTextCtrlList,
                            self.rotValCodeTextCtrlList ]                   

        curNumRows = len(self.stepTextCtrlList)      

        # Handle the situation when loading a new sequence file the has less steps - remove extra rows
        if loadNewSeq and (self.numSteps <= curNumRows):
            totTextCtrlList = contTextCtrlList + [self.stepTextCtrlList]
            for row in range(self.numSteps):
                for textCtrlList in contTextCtrlList:
                    textCtrlList[row].Enable(True)
                for elemIdx in range(self.numSolValves):    
                    self.valStateCheckboxSet[row][elemIdx].Enable(True) 
                        
            for row in range(self.numSteps, curNumRows):
                for textCtrlList in totTextCtrlList:
                    textCtrlList[row].Destroy()
                for elemIdx in range(self.numSolValves):           
                    self.valStateCheckboxSet[row][elemIdx].Destroy()   
            
            # Clean the ID lists
            self.valStateIdList = self.valStateIdList[:self.numSolValves*self.numSteps]   
            self.durationIdList = self.durationIdList[:self.numSteps]   
            self.valCodeIdList = self.valCodeIdList[:self.numSteps] 
            self.rotValCodeIdList = self.rotValCodeIdList[:self.numSteps]     
            
            # Clean the wx element lists    
            for row in range(self.numSteps, curNumRows):   
                for textCtrlList in totTextCtrlList:
                    textCtrlList.remove(textCtrlList[-1])
                self.valStateCheckboxSet.remove(self.valStateCheckboxSet[-1])
            return    
        
        # Regular situation        
        if self.numSteps < self.lastNumSteps:
            # Need to disable rows            
            for row in range(self.numSteps, self.lastNumSteps):           
                for textCtrlList in contTextCtrlList:
                    textCtrlList[row].Enable(False)
                for elemIdx in range(self.numSolValves):    
                    self.valStateCheckboxSet[row][elemIdx].Enable(False) 
                        
        elif self.lastNumSteps == self.numSteps:
            pass
            
        else:
            # Need to use more rows
            if self.numSteps <= curNumRows:
                # Only need to enable rows
                for row in range(self.lastNumSteps, self.numSteps):   
                    for textCtrlList in contTextCtrlList:
                        textCtrlList[row].Enable(True)
                    for elemIdx in range(self.numSolValves):    
                        self.valStateCheckboxSet[row][elemIdx].Enable(True)   
            else:
                # Need to add some rows
                # Enable all available rows first
                for row in range(self.lastNumSteps, curNumRows):   
                    for textCtrlList in contTextCtrlList:
                        textCtrlList[row].Enable(True)
                    for elemIdx in range(self.numSolValves):    
                        self.valStateCheckboxSet[row][elemIdx].Enable(True)  
                # Then add more rows        
                for row in range(self.numSteps-curNumRows):    
                    textCtrl = wx.TextCtrl(self.panel, -1, str(curNumRows+row+1), style=wx.TE_READONLY|wx.TE_CENTRE)
                    textCtrl.SetMinSize((80, 20))
                    textCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
                    self.stepTextCtrlList.append(textCtrl) 
                    
                    durationId = wx.NewId()
                    textCtrl = wx.TextCtrl(self.panel, durationId, "0", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
                    textCtrl.SetMinSize((100, 20))   
                    self.durationTextCtrlList.append(textCtrl)
                    self.durationIdList.append(durationId)              
                    
                    checkboxList = []
                    for idx in range(self.numSolValves):
                        cbId = wx.NewId()
                        checkbox = wx.CheckBox(self.panel, cbId, "")
                        checkbox.SetMinSize((20, 20))
                        checkboxList.append(checkbox)    
                        self.valStateIdList.append(cbId)
                    self.valStateCheckboxSet.append(checkboxList)    
                    
                    valCodeId = wx.NewId()
                    textCtrl = wx.TextCtrl(self.panel, valCodeId, "0", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
                    textCtrl.SetMinSize((100, 20))         
                    self.valCodeTextCtrlList.append(textCtrl)       
                    self.valCodeIdList.append(valCodeId)

                    rotValCodeId = wx.NewId()                    
                    textCtrl = wx.TextCtrl(self.panel, rotValCodeId, "0", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
                    textCtrl.SetMinSize((100, 20))            
                    self.rotValCodeTextCtrlList.append(textCtrl)                     
                    self.rotValCodeIdList.append(rotValCodeId)
                    
    def doLayout(self):
        sizerToplevel = wx.BoxSizer(wx.VERTICAL)
        sizerMainLayout = wx.BoxSizer(wx.VERTICAL)
        
        # Add title
        sizerMainLayout.Add(self.labelTitle, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 10)
        
        # Control section
        sizerStartDate = wx.BoxSizer(wx.HORIZONTAL)
        sizerStartTime = wx.BoxSizer(wx.HORIZONTAL)
        sizerCtrlTop = wx.FlexGridSizer(0, 4)
        sizerCtrlBottom = wx.FlexGridSizer(0, 4)
        sizerCtrl = wx.BoxSizer(wx.VERTICAL)
        
        sizerCtrlTop.Add(self.labelTotSteps, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlTop.Add(self.labelGoToStep, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlTop.Add((0,0))
        sizerCtrlTop.Add((0,0))
        sizerCtrlTop.Add(self.spinCtrlTotSteps, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlTop.Add(self.spinCtrlGoToStep, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlTop.Add(self.buttonApply, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlTop.Add(self.buttonRunNext, 0, wx.ALL|wx.EXPAND, 4)
        
        # Date/Time section
        sizerCtrlBottom.Add(self.labelStartDate, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlBottom.Add(self.labelStartTime, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlBottom.Add((0,0))
        sizerCtrlBottom.Add((0,0))
        sizerStartDate.Add((0,0))
        sizerStartDate.Add(self.ctrlStartDate, 0, wx.ALIGN_CENTER_VERTICAL)
        sizerStartTime.Add(self.ctrlStartTime, 1, wx.ALIGN_CENTER_VERTICAL)
        sizerStartTime.Add(self.spinButtonStartTime, 0, wx.ALIGN_CENTER_VERTICAL)
        sizerCtrlBottom.Add(sizerStartDate, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlBottom.Add(sizerStartTime, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlBottom.Add(self.buttonSch, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrlBottom.Add((0,0))
        
        # Combine top and bottom control panels
        sizerCtrl.Add(sizerCtrlTop, 0, wx.BOTTOM, 15)
        sizerCtrl.Add(self.staticLine2, 0, wx.EXPAND)
        sizerCtrl.Add(sizerCtrlBottom)
        
        # Show current values
        sizerDisplayAndPanel = wx.BoxSizer(wx.VERTICAL)
        sizerCurDisplay = wx.BoxSizer(wx.HORIZONTAL)
        sizerCurStep = wx.BoxSizer(wx.VERTICAL)
        sizerCurDuration = wx.BoxSizer(wx.VERTICAL)
        sizerCurValState = wx.BoxSizer(wx.VERTICAL)
        sizerCurValCode = wx.BoxSizer(wx.VERTICAL)
        sizerCurRotVal = wx.BoxSizer(wx.VERTICAL)
        sizerCurValStateChecklist = wx.BoxSizer(wx.HORIZONTAL)  
        
        sizerCurStep.Add(self.labelCurStep, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurStep.Add(self.curTextCtrlList[0], 0, wx.ALL|wx.EXPAND, 4)
        sizerCurStep.Add(self.labelStep, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDisplay.Add(sizerCurStep, 0, 0, 0)
        
        sizerCurDuration.Add(self.labelCurDuration, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDuration.Add(self.curTextCtrlList[1], 0, wx.ALL|wx.EXPAND, 4)
        sizerCurDuration.Add(self.labelDuration, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDisplay.Add(sizerCurDuration, 1, 0, 0)        
        
        sizerCurValState.Add(self.labelCurValState, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)  
        sizerCurValStateChecklist.Add(self.checkboxColorFiller, 0, wx.TOP|wx.BOTTOM, 4)        
        for idx in range(0, self.numSolValves):
            sizerCurValStateChecklist.Add(self.curCheckboxList[idx], 0, wx.TOP|wx.BOTTOM, 4)
        sizerCurValState.Add(sizerCurValStateChecklist, 1, wx.EXPAND, 0)
        sizerCurValState.Add(self.labelValState, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDisplay.Add(sizerCurValState, 1, wx.LEFT, 5)
        
        sizerCurValCode.Add(self.labelCurValCode, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurValCode.Add(self.curTextCtrlList[2], 0, wx.ALL|wx.EXPAND, 4)
        sizerCurValCode.Add(self.labelValCode, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDisplay.Add(sizerCurValCode, 1, 0, 0)
        
        sizerCurRotVal.Add(self.labelCurRotVal, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurRotVal.Add(self.curTextCtrlList[3], 0, wx.ALL|wx.EXPAND, 4)
        sizerCurRotVal.Add(self.labelRotVal, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerCurDisplay.Add(sizerCurRotVal, 1, 0, 0)
        
        sizerDisplayAndPanel.Add(sizerCurDisplay, 1, wx.RIGHT|wx.EXPAND, 20)

        # Panel layout   
        sizerPanel = wx.BoxSizer(wx.VERTICAL)
        for row in range(self.numSteps):
            sizerPanelColumn = wx.BoxSizer(wx.HORIZONTAL) 
            sizerStep = wx.BoxSizer(wx.VERTICAL)
            sizerDuration = wx.BoxSizer(wx.VERTICAL)
            sizerValState = wx.BoxSizer(wx.VERTICAL)
            sizerChecklist = wx.BoxSizer(wx.HORIZONTAL)
            sizerValCode = wx.BoxSizer(wx.VERTICAL)
            sizerRotVal = wx.BoxSizer(wx.VERTICAL) 

            sizerStep.Add(self.stepTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 4)
            sizerPanelColumn.Add(sizerStep, 0, 0, 0)       
            
            sizerDuration.Add(self.durationTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 4)
            sizerPanelColumn.Add(sizerDuration, 1, 0, 0)              
            
            checkboxList = self.valStateCheckboxSet[row]
            for idx in range(self.numSolValves):
                sizerChecklist.Add(checkboxList[idx], 0, wx.TOP|wx.BOTTOM, 4)
            sizerValState.Add(sizerChecklist, 1, wx.EXPAND, 0)
            sizerPanelColumn.Add(sizerValState, 1, wx.LEFT, 10)
            
            sizerValCode.Add(self.valCodeTextCtrlList[row], 0, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 4)
            sizerPanelColumn.Add(sizerValCode, 1, 0, 0)
            
            sizerRotVal.Add(self.rotValCodeTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 4)
            sizerPanelColumn.Add(sizerRotVal, 1, 0, 0)
            
            sizerPanel.Add(sizerPanelColumn, 0, wx.EXPAND, 0)

        self.panel.SetSizer(sizerPanel)
        
        sizerDisplayAndPanel.Add(self.panel, 4, wx.EXPAND, 0)
        
        if FORMAT_OPTION == 1:
            sizerMainLayout.Add(sizerCtrl, 0, wx.RIGHT|wx.EXPAND, 20)
            sizerMainLayout.Add(self.staticLine1, 0, wx.EXPAND, 0)
            sizerMainLayout.Add(sizerDisplayAndPanel, 0, wx.BOTTOM, 5)
        else:
            sizerMainLayout.Add(sizerDisplayAndPanel, 0, wx.BOTTOM, 5)
            #sizerMainLayout.Add(self.staticLine1, 0, wx.EXPAND, 0)
            sizerMainLayout.Add(sizerCtrl, 0, wx.EXPAND, 0)
            
        #sizerMainLayout.Add(sizerDateTime, 0, wx.EXPAND, 0)
                
        # Put everything together
        sizerToplevel.Add(sizerMainLayout, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 30)
        
        # Finalize the main frame and panel
        self.SetSizer(sizerToplevel)
        #sizerToplevel.Fit(self)
        sizerToplevel.FitInside(self)
        sizerPanel.FitInside(self.panel)      
        self.SetSize((760, 630))           
        #self.Layout()