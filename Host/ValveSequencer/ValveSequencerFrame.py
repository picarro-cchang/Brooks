# -*- coding: iso-8859-15 -*-
import wx

DEFAULT_NUM_STEPS = 10
NUM_VALVES = 6
FORMAT_OPTION = 2

class ValveSequencerFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.numSteps = DEFAULT_NUM_STEPS 
        self.lastNumSteps = 0
        
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
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
        menuItem.Append(self.idLoadFile, "Load Valve Sequence File", "", wx.ITEM_NORMAL)
        menuItem.Append(self.idSaveFile, "Save Valve Sequence File", "", wx.ITEM_NORMAL)
        self.frameMenubar.Append(menuItem, "File")
        menuItem = wx.Menu()
        menuItem.Append(self.idEnableSeq, "Enable Sequencer", "", wx.ITEM_NORMAL)
        #menuItem.Append(self.idDisableSeq, "Disable Sequencer", "", wx.ITEM_NORMAL)
        menuItem.Append(self.idGoFirstStep, "Go To First Step", "", wx.ITEM_NORMAL)        
        self.frameMenubar.Append(menuItem, "Action")
        self.SetMenuBar(self.frameMenubar)
        
        # Labels
        self.labelTitle = wx.StaticText(self, -1, "External Valve Sequencer", style=wx.ALIGN_CENTRE)
        self.labelTotSteps = wx.StaticText(self, -1, "Total Steps", style=wx.ALIGN_CENTRE)
        self.labelGoToStep = wx.StaticText(self, -1, "Run Step #", style=wx.ALIGN_CENTRE)
        self.labelBlank = wx.StaticText(self, -1, "", style=wx.ALIGN_CENTRE)
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
        self.spinCtrlTotSteps = wx.SpinCtrl(self, -1, str(self.numSteps), min=1, max=50, style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)        
        self.spinCtrlGoToStep = wx.SpinCtrl(self, -1, "1", min=1, max=50, style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)

        self.buttonApply = wx.Button(self, -1, "Apply", style=wx.BU_EXACTFIT)        
        self.buttonRunNext = wx.Button(self, -1, "Run Next Step", style=wx.BU_EXACTFIT)

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
        for idx in range(NUM_VALVES):
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
        self.staticLine = wx.StaticLine(self, -1)      
        
        # Overall properties
        self.SetTitle("External Valve Sequencer")
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.labelTitle.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.panel.SetScrollRate(10, 10)
        
        # Button properties                    
        self.buttonRunNext.SetMinSize((100, 20))
        self.buttonRunNext.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonRunNext.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonApply.SetMinSize((100, 20))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonApply.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))

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
                for elemIdx in range(NUM_VALVES):    
                    self.valStateCheckboxSet[row][elemIdx].Enable(True) 
                        
            for row in range(self.numSteps, curNumRows):
                for textCtrlList in totTextCtrlList:
                    textCtrlList[row].Destroy()
                for elemIdx in range(NUM_VALVES):           
                    self.valStateCheckboxSet[row][elemIdx].Destroy()   
            
            # Clean the ID lists
            self.valStateIdList = self.valStateIdList[:NUM_VALVES*self.numSteps]   
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
                for elemIdx in range(NUM_VALVES):    
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
                    for elemIdx in range(NUM_VALVES):    
                        self.valStateCheckboxSet[row][elemIdx].Enable(True)   
            else:
                # Need to add some rows
                # Enable all available rows first
                for row in range(self.lastNumSteps, curNumRows):   
                    for textCtrlList in contTextCtrlList:
                        textCtrlList[row].Enable(True)
                    for elemIdx in range(NUM_VALVES):    
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
                    for idx in range(NUM_VALVES):
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
        sizerCtrl = wx.BoxSizer(wx.HORIZONTAL)
        sizerTotSteps = wx.BoxSizer(wx.VERTICAL)
        sizerGoToStep = wx.BoxSizer(wx.VERTICAL)
        sizerApply = wx.BoxSizer(wx.VERTICAL)
        sizerRunNext = wx.BoxSizer(wx.VERTICAL)
        
        sizerTotSteps.Add(self.labelTotSteps, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerTotSteps.Add(self.spinCtrlTotSteps, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrl.Add(sizerTotSteps, 1, 0, 0)
        
        sizerGoToStep.Add(self.labelGoToStep, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerGoToStep.Add(self.spinCtrlGoToStep, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrl.Add(sizerGoToStep, 1, 0, 0)

        sizerApply.Add(self.labelBlank, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerApply.Add(self.buttonApply, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrl.Add(sizerApply, 1, 0, 0)
        
        sizerRunNext.Add(self.labelBlank, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizerRunNext.Add(self.buttonRunNext, 0, wx.ALL|wx.EXPAND, 4)
        sizerCtrl.Add(sizerRunNext, 1, 0, 0)

        if FORMAT_OPTION == 1:
            sizerMainLayout.Add(sizerCtrl, 0, wx.RIGHT|wx.EXPAND, 20)
            sizerMainLayout.Add(self.staticLine, 0, wx.EXPAND, 0)
        
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
        for idx in range(0, NUM_VALVES):
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
            for idx in range(NUM_VALVES):
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
        
        # Combine current info and panel
        sizerMainLayout.Add(sizerDisplayAndPanel, 0, wx.BOTTOM, 5)
        
        if FORMAT_OPTION == 2:
            sizerMainLayout.Add(self.staticLine, 0, wx.EXPAND, 0)
            sizerMainLayout.Add(sizerCtrl, 0, wx.EXPAND, 0)
                
        # Put everything together
        sizerToplevel.Add(sizerMainLayout, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 30)
        
        # Finalize the main frame and panel
        self.SetSizer(sizerToplevel)
        #sizerToplevel.Fit(self)
        sizerToplevel.FitInside(self)
        sizerPanel.FitInside(self.panel)      
        self.SetSize((760, 575))           
        #self.Layout()