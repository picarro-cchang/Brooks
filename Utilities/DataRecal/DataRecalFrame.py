# -*- coding: iso-8859-15 -*-
import wx

DEFAULT_NUM_ROWS = 10

class DataRecalFrame(wx.Frame):
    def __init__(self, dataList, *args, **kwds):
        self.numRows = DEFAULT_NUM_ROWS 
        
        #kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        kwds["style"] = wx.CAPTION|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.panel3.SetBackgroundColour("#43C6DB")
        
        # Divider line
        self.staticLine1 = wx.StaticLine(self, -1) 
        self.staticLine2 = wx.StaticLine(self, -1) 
        
        # Menu bar
        self.frameMenubar = wx.MenuBar()
        menuItem = wx.Menu()
        self.idLoadFile = wx.NewId()
        self.idSaveFile = wx.NewId()
        self.iLoadFile = wx.MenuItem(menuItem, self.idLoadFile, "Load Recalibration File", "", wx.ITEM_NORMAL)
        menuItem.AppendItem(self.iLoadFile)
        self.frameMenubar.Append(menuItem, "File")
        menuItem = wx.Menu()
        self.idPlotFit = wx.NewId()
        self.iPlotFit = wx.MenuItem(menuItem, self.idPlotFit, "Plot Linear Fitting", "", wx.ITEM_NORMAL)        
        menuItem.AppendItem(self.iPlotFit)
        self.frameMenubar.Append(menuItem, "Plot")
        self.SetMenuBar(self.frameMenubar)
        
        # Title and column labels
        self.labelTitle = wx.StaticText(self.panel1, -1, "Picarro Data Recalibration", style=wx.ALIGN_CENTRE)
        self.labelRecalSel = wx.StaticText(self.panel1, -1, "Used for Recal", style=wx.ALIGN_CENTRE)        
        self.labelAccept = wx.StaticText(self.panel1, -1, "Certified", style=wx.ALIGN_CENTRE)
        self.labelReport = wx.StaticText(self.panel1, -1, "CRDS Reported", style=wx.ALIGN_CENTRE)
        self.labelRecal = wx.StaticText(self.panel1, -1, "Recalibrated", style=wx.ALIGN_CENTRE)

        # Overall properties
        self.SetTitle("Picarro Data Recalibration")
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)
        
        # Column text controls
        self.acceptTextCtrlList = []
        self.reportTextCtrlList = []
        self.recalTextCtrlList = []
        self.checkboxList = []
        
        for row in range(self.numRows):
            acceptId = wx.NewId()
            textCtrl = wx.TextCtrl(self.panel1, acceptId, "0.00000", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
            self.acceptTextCtrlList.append(textCtrl) 
            
            reportId = wx.NewId()
            textCtrl = wx.TextCtrl(self.panel1, reportId, "0.00000", style=wx.TE_PROCESS_ENTER|wx.TE_CENTRE)
            self.reportTextCtrlList.append(textCtrl)          
            
            recalId = wx.NewId()
            textCtrl = wx.TextCtrl(self.panel1, recalId, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
            textCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
            self.recalTextCtrlList.append(textCtrl)  
            
            cbId = wx.NewId()
            checkbox = wx.CheckBox(self.panel1, cbId, "")
            checkbox.SetMinSize((20, 20))
            self.checkboxList.append(checkbox)    
        
        # The calibration value table
        self.labelOption= wx.StaticText(self.panel2, -1, "Calibration Options", style=wx.ALIGN_CENTRE)
        self.labelData= wx.StaticText(self.panel2, -1, "Data Options", style=wx.ALIGN_CENTRE)
        self.labelCurCal = wx.StaticText(self.panel2, -1, "Current Calibration", style=wx.ALIGN_CENTRE)
        self.labelNewCal = wx.StaticText(self.panel2, -1, "New Calibration", style=wx.ALIGN_CENTRE)
        self.labelOffset = wx.StaticText(self.panel2, -1, "Offset", style=wx.ALIGN_CENTRE)
        self.labelSlope = wx.StaticText(self.panel2, -1, "Slope", style=wx.ALIGN_CENTRE)
        self.labelR2 = wx.StaticText(self.panel2, -1, "R2", style=wx.ALIGN_CENTRE)
        self.optionComboBox = wx.ComboBox(self.panel2, -1, value = " Offset Only", choices = [" Offset Only", " Offset + Slope"], style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.dataComboBox = wx.ComboBox(self.panel2, -1, value = dataList[0], choices = dataList, style = wx.CB_READONLY|wx.CB_DROPDOWN)
        self.curOffsetTextCtrl = wx.TextCtrl(self.panel2, -1, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
        self.curSlopeTextCtrl = wx.TextCtrl(self.panel2, -1, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
        self.newOffsetTextCtrl = wx.TextCtrl(self.panel2, -1, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
        self.newSlopeTextCtrl = wx.TextCtrl(self.panel2, -1, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
        self.r2TextCtrl = wx.TextCtrl(self.panel2, -1, "0.00000", style=wx.TE_READONLY|wx.TE_CENTRE)
        self.curOffsetTextCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
        self.curSlopeTextCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
        self.newOffsetTextCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
        self.newSlopeTextCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 
        self.r2TextCtrl.SetBackgroundColour(wx.Colour(206, 206, 206)) 

        # Buttons
        self.buttonCompute = wx.Button(self.panel3, -1, "Compute", style=wx.BU_EXACTFIT)
        self.buttonApply = wx.Button(self.panel3, -1, "Apply New Cal", style=wx.BU_EXACTFIT)       
        self.buttonClear = wx.Button(self.panel3, -1, "Clear Entries", style=wx.BU_EXACTFIT)         
        self.buttonExit = wx.Button(self.panel3, -1, "Exit", style=wx.BU_EXACTFIT) 
        self.buttonCompute.SetMinSize((60, 20))
        self.buttonCompute.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonCompute.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonApply.SetMinSize((60, 20))
        self.buttonApply.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonApply.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonClear.SetMinSize((60, 20))
        self.buttonClear.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonClear.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonExit.SetMinSize((60, 20))
        self.buttonExit.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonExit.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        self.doLayout()
  
    def doLayout(self):
        sizerToplevel = wx.BoxSizer(wx.VERTICAL)
        sizerMainLayout = wx.BoxSizer(wx.VERTICAL)
        
        # Panel layout
        sizerPanel1 = wx.BoxSizer(wx.VERTICAL)
        sizerPanel1Margin = wx.BoxSizer(wx.VERTICAL)
        sizerColTitles = wx.BoxSizer(wx.HORIZONTAL)
        
        sizerPanel1.Add(self.labelTitle, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizerColTitles.Add(self.labelRecalSel, 0, wx.LEFT|wx.RIGHT, 20)
        sizerColTitles.Add(self.labelAccept, 0, wx.LEFT|wx.RIGHT, 32)
        sizerColTitles.Add(self.labelReport, 0, wx.LEFT|wx.RIGHT, 22)
        sizerColTitles.Add(self.labelRecal, 0, wx.LEFT|wx.RIGHT, 20)
        sizerPanel1.Add(sizerColTitles, 0, wx.EXPAND, 0)
        for row in range(self.numRows):
            sizerPanel1Column = wx.BoxSizer(wx.HORIZONTAL) 
            sizerChecklist = wx.BoxSizer(wx.HORIZONTAL)
            sizerChecklist.Add((50,-1),0)
            sizerChecklist.Add(self.checkboxList[row], 0, wx.TOP|wx.BOTTOM, 5)
            sizerChecklist.Add((40,-1),0)
            sizerPanel1Column.Add(sizerChecklist, 0, wx.EXPAND)
            sizerPanel1Column.Add(self.acceptTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 5)       
            sizerPanel1Column.Add(self.reportTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 5)              
            sizerPanel1Column.Add(self.recalTextCtrlList[row], 0, wx.ALL|wx.EXPAND, 5)    
            sizerPanel1.Add(sizerPanel1Column, 0, wx.EXPAND|wx.BOTTOM, 10)
        sizerPanel1Margin.Add(sizerPanel1, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 20)
        self.panel1.SetSizer(sizerPanel1Margin)
        sizerMainLayout.Add(self.panel1, 0, wx.EXPAND, 0)
        sizerMainLayout.Add(self.staticLine1, 0, wx.EXPAND, 0)
        
        # Add calibration table
        sizerPanel2 = wx.BoxSizer(wx.VERTICAL)
        sizerPanel2Margin = wx.BoxSizer(wx.VERTICAL)
        sizerSpace1 = wx.BoxSizer(wx.VERTICAL)
        sizerSpace2 = wx.BoxSizer(wx.VERTICAL)
        sizerSpace3 = wx.BoxSizer(wx.VERTICAL)
        sizerComboBox1 = wx.BoxSizer(wx.VERTICAL)
        sizerComboBox2 = wx.BoxSizer(wx.VERTICAL) 
        grid_sizer = wx.FlexGridSizer(-1, 5)
        addSpacer = (40,0)
        
        sizerSpace1.Add(self.labelData, 0, wx.TOP|wx.ALIGN_BOTTOM|wx.ALIGN_LEFT, 10)
        grid_sizer.Add(sizerSpace1, 0, wx.LEFT, 22)
        grid_sizer.Add((0,0))
        grid_sizer.Add(addSpacer)
        grid_sizer.Add(self.labelCurCal, 0, wx.TOP|wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 10)
        sizerSpace2.Add(self.labelNewCal, 0, wx.TOP|wx.ALIGN_BOTTOM|wx.ALIGN_LEFT, 10)
        grid_sizer.Add(sizerSpace2, 0, wx.LEFT, 12)
        
        sizerComboBox1.Add(self.dataComboBox, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer.Add(sizerComboBox1, 0, wx.LEFT, 10)
        grid_sizer.Add(addSpacer)
        grid_sizer.Add(self.labelOffset, 0, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
        grid_sizer.Add(self.curOffsetTextCtrl, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer.Add(self.newOffsetTextCtrl, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)

        sizerSpace3.Add(self.labelOption, 0, wx.TOP|wx.ALIGN_BOTTOM|wx.ALIGN_LEFT, 15)
        grid_sizer.Add(sizerSpace3, 0, wx.LEFT, 22)
        grid_sizer.Add(addSpacer)
        grid_sizer.Add(self.labelSlope, 0, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
        grid_sizer.Add(self.curSlopeTextCtrl, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer.Add(self.newSlopeTextCtrl, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        
        sizerComboBox2.Add(self.optionComboBox, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer.Add(sizerComboBox2, 0, wx.LEFT, 10)
        grid_sizer.Add(addSpacer)
        grid_sizer.Add(self.labelR2, 0, wx.LEFT|wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 10)
        grid_sizer.Add((80,10))
        grid_sizer.Add(self.r2TextCtrl, 0, wx.RIGHT|wx.TOP|wx.ALIGN_CENTER_VERTICAL, 10)
        
        sizerPanel2.Add(grid_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        sizerPanel2Margin.Add(sizerPanel2, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 20)
        self.panel2.SetSizer(sizerPanel2Margin)
        sizerMainLayout.Add(self.panel2, 0, wx.EXPAND, 0)
        sizerMainLayout.Add(self.staticLine2, 0, wx.EXPAND, 0)
        
        # Control button section
        sizerPanel3 = wx.BoxSizer(wx.HORIZONTAL)
        sizerPanel3Margin = wx.BoxSizer(wx.VERTICAL)

        sizerPanel3.Add(self.buttonCompute, 1, wx.ALL|wx.EXPAND, 4)
        sizerPanel3.Add(self.buttonApply, 1, wx.ALL|wx.EXPAND, 4)
        sizerPanel3.Add(self.buttonClear, 1, wx.ALL|wx.EXPAND, 4)
        sizerPanel3.Add(self.buttonExit, 1, wx.ALL|wx.EXPAND, 4)
        sizerPanel3Margin.Add(sizerPanel3, 0, wx.EXPAND|wx.ALL, 10)
        sizerPanel3Margin.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM, 5)
        self.panel3.SetSizer(sizerPanel3Margin)
        sizerMainLayout.Add(self.panel3, 0, wx.EXPAND)
                
        # Put everything together
        sizerToplevel.Add(sizerMainLayout, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 0)
        
        # Finalize the main frame and panel
        self.SetSizer(sizerToplevel)
        sizerToplevel.Fit(self)     
        self.Layout()
        
if __name__ == "__main__":
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = DataRecalFrame(["Delta_Raw"], None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()