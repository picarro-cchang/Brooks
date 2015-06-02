#@+leo-ver=4-thin
#@+node:stan.20080530161647.1:@thin AutosamplerParameterDialog.py
#!/usr/bin/python
#
# File Name: AutosamplerParameterDialog.py
# Purpose: Creates the dialog boxes for editing parameter values
#
# Notes:
#
# File History:
# 08-05-30 sze  Initial Release

# Silverstone CRDS Controller
# (c) Picarro, Inc., 2009

import wx
import wx.grid

nameCol = 0
valueCol = 1
minimumCol = 2
maximumCol = 3
defaultCol = 4
unitsCol = 5

class ParameterGrid(wx.grid.Grid):
    """ Grid for editing parameter values. The grid has three columns for the parameter name,
        the value and its units. Only cells in the value column may be edited, and navigation
        between parameters can be done via the keyboard using TAB and SHIFT-TAB """

    def __init__(self,parent,id,nrows,**kwds):
        """ Creates grid with "nrows" rows """
        wx.grid.Grid.__init__(self,parent,id,**kwds)
        self.CreateGrid(nrows, 6)   # Six columns in grid
        self.SetRowLabelSize(0)     # No row labels
        self.EnableDragColSize(0)   # Cannot resize
        self.EnableDragRowSize(0)
        self.EnableDragGridSize(0)
        # Column labels
        self.SetColLabelValue(nameCol, "Name")
        self.SetColLabelValue(valueCol, "Parameter Value")
        self.SetColLabelValue(minimumCol, "Minimum")
        self.SetColLabelValue(maximumCol, "Maximum")
        self.SetColLabelValue(defaultCol, "Default")
        self.SetColLabelValue(unitsCol, "Units")
        # Register event handlers
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnShowPopUp)

    def OnShowPopUp(self,event):
        pos = event.GetPosition()
        self.SetGridCursor(event.GetRow(),valueCol)

        event.Skip()

    def OnIdle(self,e):
        """ Prevent cursor from moving away from value column """
        col = self.GetGridCursorCol()
        if col>=0 and col != valueCol:
            row = self.GetGridCursorRow()
            self.SetGridCursor(row,valueCol)
        else: e.Skip()
    def OnKeyDown(self, e):
        """ Allow TAB and SHIFT TAB to be used for navigating between parameters """
        if e.KeyCode == wx.WXK_TAB:
            if e.ShiftDown(): self.MoveCursorUp(False)
            else: self.MoveCursorDown(False)
            return
        else: e.Skip()

class ParameterDialogBase(wx.Dialog):
    """ Dialog box for examining and editing parameters of CRDS engine """
    def __init__(self,parent,id,descr = (None,[]),**kwds):
        """ Initialize parameter names, units and choice variable drop-down boxes
            using information from descr.

            The tuple descr consists of the title of the dialog
            box together with a list describing what goes inside the box. The list consists of a
            collection of tuples, one for each software register to be displayed, i.e.,

            descr = (title_of_dialog_box,[(reg_1_details),(reg_2_details),(reg_3_details),...])

            The details tuple for a register has differing forms, depending on the type of the register

            ("int",label,units,format,optional)

            These are for registers containing integer or floating point values respectively.

              reg is the index of the register containing the parameter
              label is the string for the parameter name
              units is the string specifying the units of the parameter
              format is the format string used to represent the parameter value in the form
              readable indicates if the register may be read
              writable indicates if the register may be written

            ("choices",label,units,choice_list,optional)

            This produces a drop-down combo box of choices which the user may select from if the
            register is writable. If the register is only readable, the choice_list specifies the
            strings that are displayed in the value column.

              The choice_list is a list of choices [(value_1,string_1),(value_2,string_2),...]

            When the register has the value value_n, string_n is displayed in the parameter form.
            If the register value is not one of those specified, "-- Invalid (%x) --" is displayed
            where %x is the hexadecimal representation of the (unknown) value in the register.

            If a choice register is write-only, an additional option "-- Do not write --" is included
            in the combo box. If this option is selected, that register is not written to on
            Apply or Commit.

            ("mask",reg,bitfields,None,None,readable,writable)

            This is used for a register which contains one or more bitfields representing a collection
            of parameters. Several lines in the parameter form are created for such a register, one for
            each field.

            The bitfields element is a list of tuples, one for each field, i.e.,

            bitfields = [(mask_1,field_name_1,field_list_1),(mask_2,field_name_2,field_list_2),...]

            mask_n is the mask which is bitwise ANDed with the register contents to extract the n'th field.
            field_name_n is the string describing the n'th field which will be displayed in the parameter form.
            field_list_n specifies the list of valid contents in the field, and the string that is to be displayed
              (in a drop down combo box) for that field. Note that the values are the result of ANDing the mask
              with the contents without any shifting. Thus for a single-bit field, the values should be 0 and mask.

            The format of each field_list is [(value_1,string_1),(value_2,string_2),...]
        """
        self.title,self.details = descr
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE     # No window resize, minimize or maximize
        wx.Dialog.__init__(self,parent,id,"",**kwds)
        # Initialize the widgets on the form
        self.clist = {}   # Dictionary of choice captions, indexed by register
        self.vlist = {}   # Dictionary of choice values, indexed by register
        self.grid_1 = ParameterGrid(self,-1,self.__calc_nrows(), size=(1, 1))
        self.bCommit = wx.Button(self, -1, "Commit")
        self.bApply = wx.Button(self, -1, "Apply")
        self.bDiscard = wx.Button(self, -1, "Discard")
        self.__set_properties()
        grid_size = self.__fill_grid()
        self.__do_layout(grid_size)
        self.parameter_values = None    # To be filled with current parameter values
        # Event handlers
        self.Bind(wx.EVT_BUTTON, self.OnCommit, self.bCommit)
        self.Bind(wx.EVT_BUTTON, self.OnApply, self.bApply)
        self.Bind(wx.EVT_BUTTON, self.OnDiscard, self.bDiscard)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def __calc_nrows(self):
        "Determine number of rows in parameter grid"
        return len(self.details)

    def __set_properties(self):
        self.SetTitle(self.title)
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))

    def __do_layout(self,grid_size):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.grid_1, 1, wx.EXPAND, 0)
        sizer_2.Add(self.bCommit, 0, wx.FIXED_MINSIZE, 0)
        sizer_2.Add((30, 20), 0, wx.FIXED_MINSIZE, 0)
        sizer_2.Add(self.bApply, 0, wx.FIXED_MINSIZE, 0)
        sizer_2.Add((30, 20), 0, wx.FIXED_MINSIZE, 0)
        sizer_2.Add(self.bDiscard, 0, wx.FIXED_MINSIZE, 0)
        sizer_1.Add(sizer_2, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 15)
        sizer_1.SetItemMinSize(0,grid_size)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Fit()

    def __set_color(self,row,optional):
        """ Blue text indicates an optional quantity,
            Normal text is black """
        if optional:
            self.grid_1.SetCellTextColour(row, nameCol, wx.BLUE)
            self.grid_1.SetCellTextColour(row, valueCol, wx.BLUE)
            self.grid_1.SetCellTextColour(row, minimumCol, wx.BLUE)
            self.grid_1.SetCellTextColour(row, maximumCol, wx.BLUE)
            self.grid_1.SetCellTextColour(row, defaultCol, wx.BLUE)
            self.grid_1.SetCellTextColour(row, unitsCol, wx.BLUE)

    def __fill_grid(self):
        """ Fill in the parameter names, units and drop-down boxes for a parameter dialog,
            and adjust the grid size to be large enough for all parameters to be completely visible.
            Returns size of grid """
        row = 0
        for param in self.details:
            type,label,format,units,optional,minVal,maxVal,defVal = param
            if units == None: units = ''
            if format == None: format = ''
            self.grid_1.SetCellValue(row,nameCol,label)
            self.grid_1.SetReadOnly(row,nameCol)
            self.grid_1.SetCellValue(row,minimumCol,minVal)
            self.grid_1.SetReadOnly(row,unitsCol)
            self.grid_1.SetCellValue(row,maximumCol,maxVal)
            self.grid_1.SetReadOnly(row,maximumCol)
            self.grid_1.SetCellValue(row,defaultCol,defVal)
            self.grid_1.SetReadOnly(row,defaultCol)
            self.grid_1.SetCellValue(row,unitsCol,units)
            self.grid_1.SetReadOnly(row,unitsCol)
            if type == 'choices':
                editor = wx.grid.GridCellChoiceEditor(format,False)
                longest = 0
                lmax = 0
                # Select the longest string so that the size is adequate for all choices
                for str in format:
                    if len(str)>lmax :
                        lmax = len(str)
                        longest = str
                self.grid_1.SetCellValue(row,valueCol,longest)
                self.grid_1.SetCellEditor(row,valueCol,editor)
            self.__set_color(row,optional)
            row += 1

        self.grid_1.AutoSize()  # Autosize adjusts size to fit CURRENT strings
        tot_width = 0
        tot_height = 0
        widths = []
        for i in range(self.grid_1.GetNumberCols()):
            width = self.grid_1.GetColSize(i)
            widths.append(width)
            tot_width += width
        # Proportionally increase column widths until total width exceeds 800
        scale = max(800.0,tot_width)/tot_width
        tot_width = 0
        for i in range(self.grid_1.GetNumberCols()):
            self.grid_1.SetColSize(i,scale * widths[i])
            width = self.grid_1.GetColSize(i)
            tot_width += width
        for i in range(self.grid_1.GetNumberRows()):
            tot_height += self.grid_1.GetRowSize(i)
        # Find total height and widith of grid, and add 18 to each so that scroll bars do not appear
        return (tot_width+self.grid_1.GetRowLabelSize()+18,tot_height+self.grid_1.GetColLabelSize()+18)

    def __fill_values(self):
        """ Fill the dialog form value fields with parameter values """
        row = 0     # Row in dialog form
        indx = 0    # Index into list of registers
        for param in self.details:
            type,label,format,units,optional,minVal,maxVal,defVal = param
            val = self.parameter_values[indx]
            if type == 'int':
                if val == None:
                    self.grid_1.SetCellValue(row,valueCol,"")
                else:
                    self.grid_1.SetCellValue(row,valueCol,format % val)
            elif type == 'choices':
                self.grid_1.SetCellValue(row,valueCol,val)
                row += 1
            indx += 1

    def __validate_data(self):
        """ Validate data using information about the data type or the list of choices given.
            Return None if validation succeeds, or the row of the first invalid parameter """
        from string import strip
        new_parameter_values = []
        row = 0
        for param in self.details:
            type,reg,label,units,format,readable,writable = param
            value = None
            if writable:
                if type == "mask":
                    mask = 0
                    value = 0
                    for bitfields in label:
                        valueAsText = strip(self.grid_1.GetCellValue(row,valueCol))
                        bitmask,label,choices = bitfields
                        mask |= bitmask
    #          print "Bitmask: %x, valueAsText: %s" % (bitmask,valueAsText)
                        try:
                            value |= self.vlist[reg][bitmask][self.clist[reg][bitmask].index(valueAsText)]   # Check against list of valid choices in format
                        except:
                            return row
                        row += 1
                    value = (value,mask)
                else:
                    valueAsText = strip(self.grid_1.GetCellValue(row,1))
                    if valueAsText == None or (valueAsText == '' and type != 'choices'):
                        pass
                    elif type == 'int':
                        try:
                            if valueAsText[0] == '$':   # hexadecimal
                                value = int(valueAsText[1:],16)
                            else:
                                value = int(valueAsText)
                        except:
                            return row
                    elif type == 'float':
                        try:
                            value = float(valueAsText)
                        except:
                            return row
                    elif type == 'choices':
                        try:
                            value = self.vlist[reg][self.clist[reg].index(valueAsText)]   # Check against list of valid choices in format
                        except:
                            return row
                    row += 1
            else:
                if type == "mask":
                    row += len(label)
                else:
                    row += 1
            new_parameter_values.append(value)
        self.parameter_values = new_parameter_values    # Only update stored values if all are valid
        return None

    def OnCommit(self,e):
        """ Validate parameter values, write them to DAS if valid, and destroy form """
        self.grid_1.DisableCellEditControl()
        #bad = self.__validate_data()
        bad = None
        if bad == None:
            print "Transfer data here!"
            self.Destroy()
        else:   # Highlight the first invalid parameter value
            self.grid_1.SetGridCursor(bad,valueCol)
            self.grid_1.SetFocus()

    def OnApply(self,e):
        """ Validate parameter values, write them to DAS if valid, and re-read values
            leaving form open """
        self.grid_1.DisableCellEditControl()
        # bad = self.__validate_data()
        bad = None
        if bad == None:
            print "Transfer data and retrieve new"
        else:
            self.grid_1.SetGridCursor(bad,valueCol)
            self.grid_1.SetFocus()

    def OnDiscard(self,e):
        """ Just destroy the form, discarding changes """
        self.Destroy()

    def OnClose(self,e):
        """ Just destroy the form, discarding changes """
        self.Destroy()

    def ReadFromDas(self):
        """ Read parameters from DAS in order to fill up form with current values"""
        regList = [param[1] for param in self.details if param[5]]
        badList = [i for i in range(len(self.details)) if not self.details[i][5]]
        valueList = regList
        for b in badList: valueList.insert(b,None)
        self.parameter_values = valueList
        self.__fill_values()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()

    parameter_forms = []
    __p = [("choices","Injected Signal","Min","Max","Def","",["Apple","Bear"],False),
           ("int","Penetration","0.0","1.0","0.5","um","%.0f",True),]

    parameter_forms.append(('Inject Sample',__p))

    frame_1 = ParameterDialogBase(None, -1, descr=parameter_forms[0])
    #frame_1.ReadFromDas()

    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
#@-node:stan.20080530161647.1:@thin AutosamplerParameterDialog.py
#@-leo