#!/usr/bin/python
#
# FILE:
#   ParameterDialog.py
#
# DESCRIPTION:
#   Generate parameter dialogs for examining and changing software registers
#    on the DAS
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   06-Jan-2009  sze  Initial version.
#   30-Jun-2009  sze  Modifications to allow access to FPGA registers as 
#                      well as DSP registers
#
#  Copyright (c) 2009 Picarro, Inc. All rights reserved
#

import wx
import ctypes

from ParameterDialogGui import ParameterDialogGui

class ParameterDialog(ParameterDialogGui):
    def __init__(self, *args, **kwds):
        ParameterDialogGui.__init__(self,*args,**kwds)
        self.Bind(wx.EVT_CLOSE, self.onClose)

    def initialize(self,title,details):
        """ Initialize parameter names, units and choice variable drop-down boxes
            using information from descr.

            "title" consists of the title of the dialog box

            "details" is a list describing what goes inside the dialog. The list consists of a
            collection of tuples, one for each software register to be displayed, i.e.,

            details = [(reg_1_details),(reg_2_details),(reg_3_details),...]

            The details tuple for a register has differing forms, depending on the type of the register

            (regLoc,"uint16",reg,label,units,format,readable,writable)
            (regLoc,"int16",reg,label,units,format,readable,writable)
            (regLoc,"uint32",reg,label,units,format,readable,writable)
            (regLoc,"int32",reg,label,units,format,readable,writable)
            (regLoc,"float",reg,label,units,format,readable,writable)

            These are for registers containing integer or floating point values respectively.

              regLoc is location of register, currently "dsp" or "fpga"
              reg is the index of the register containing the parameter
              label is the string for the parameter name
              units is the string specifying the units of the parameter
              format is the format string used to represent the parameter value in the form
              readable indicates if the register may be read
              writable indicates if the register may be written

            (regLoc,"choices",reg,label,units,choice_list,readable,writable)

            This produces a drop-down combo box of choices which the user may select from if the
            register is writable. If the register is only readable, the choice_list specifies the
            strings that are displayed in the value column.

              The choice_list is a list of tuples [(value_1,string_1),(value_2,string_2),...]

            When the register has the value value_n, string_n is displayed in the parameter form.
            If the register value is not one of those specified, "-- Invalid (%x) --" is displayed
            where %x is the hexadecimal representation of the (unknown) value in the register.

            If a choice register is write-only, an additional option "-- Do not write --" is included
            in the combo box. If this option is selected, that register is not written to on
            Apply or Commit.

            (regLoc,"mask",reg,bitfields,None,None,readable,writable)

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
        self.title = title
        self.details = details
        self.SetTitle(self.title)
        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE))
        # Initialize the widgets on the form
        self.parameterGrid.makeGrid(self.calcRows())
        self.clist = {}   # Dictionary of choice captions, indexed by register
        self.vlist = {}   # Dictionary of choice values, indexed by register
        self.paramValues = None    # To be filled with current parameter values
        grid_size = self.fillGrid()
        self.doLayout(grid_size)

    def calcRows(self):
        "Determine number of rows in parameter grid"
        rows = 0
        for param in self.details:
            regLoc,regType,reg,label,units,valueFmt,readable,writable = param
            if regType == 'mask':
                # For mask type, the bits are stored as a list of tuples in the label field.
                #  The choices for each field are stored in the last position of the tuple. 
                #  If this is an empty list, that does not contribute to a row
                #  There are thus as many rows for this register as elements in the list
                rows += len([1 for bitmask,label,choices in label if choices])
            else:
                rows += 1
        return rows

    def setColor(self,row,readable,writable):
        """ Red text indicates a read-only quantity,
            Blue text indicates a write-only quantity,
            Normal text (read-write registers) is black """
        grid = self.parameterGrid
        if readable and not writable:
            grid.SetCellTextColour(row, 0, wx.RED)
            grid.SetCellTextColour(row, 1, wx.RED)
            grid.SetCellTextColour(row, 2, wx.RED)
            grid.SetReadOnly(row,1)
        if writable and not readable:
            grid.SetCellTextColour(row, 0, wx.BLUE)
            grid.SetCellTextColour(row, 1, wx.BLUE)
            grid.SetCellTextColour(row, 2, wx.BLUE)

    def handleMaskRegister(self,row,reg,label,readable,writable):
        grid = self.parameterGrid
        self.vlist[reg] = {}
        self.clist[reg] = {}
        for bitfields in label:
            bitmask,label,choices = bitfields
            if choices:
                self.vlist[reg][bitmask] = [c[0] for c in choices]
                self.clist[reg][bitmask] = [c[1] for c in choices]
                grid.SetCellValue(row,0,label)
                grid.SetReadOnly(row,0)
                grid.SetReadOnly(row,2)
                editor = wx.grid.GridCellChoiceEditor(self.clist[reg][bitmask],False)
                longest = 0
                lmax = 0
                # Select the longest string so that the size is adequate for all choices
                for str in self.clist[reg][bitmask]:
                    if len(str)>lmax :
                        lmax = len(str)
                        longest = str
                grid.SetCellValue(row,1,longest)
                grid.SetCellEditor(row,1,editor)
                self.setColor(row,readable,writable)
                row += 1
        return row

    def handleChoiceRegister(self,row,reg,choices,readable,writable):
        grid = self.parameterGrid
        self.vlist[reg] = [f[0] for f in choices]
        self.clist[reg] = [f[1] for f in choices]
        if writable and not readable:
            self.vlist[reg][:0] = [None]
            self.clist[reg][:0] = ["-- Do not write --"]
        editor = wx.grid.GridCellChoiceEditor(self.clist[reg],False)
        longest = 0
        lmax = 0
        # Select the longest string so that the size is adequate for all choices
        for str in self.clist[reg]:
            if len(str)>lmax :
                lmax = len(str)
                longest = str
        grid.SetCellValue(row,1,longest)
        grid.SetCellEditor(row,1,editor)

    def fillGrid(self):
        """ Fill in the parameter names, units and drop-down boxes for a parameter dialog,
            and adjust the grid size to be large enough for all parameters to be completely visible.
            Returns size of grid """
        grid = self.parameterGrid
        row = 0
        for param in self.details:
            regLoc,regType,reg,label,units,valueFmt,readable,writable = param
            if units == None: units = ''
            if valueFmt == None: valueFmt = ''
            if regType == 'mask':
                # For mask type, the bits to be displayed are stored in the label field
                row = self.handleMaskRegister(row,reg,label,readable,writable)
            else:
                # Non-mask registers may store a value, or a set of choices
                grid.SetCellValue(row,0,label)
                grid.SetReadOnly(row,0)
                grid.SetCellValue(row,2,units)
                grid.SetReadOnly(row,2)
                if regType == "choices":
                    # choices are stored in the valueFmt field for a choice register
                    self.handleChoiceRegister(row,reg,valueFmt,readable,writable)
                self.setColor(row,readable,writable)
                row += 1

        grid.AutoSize()  # Autosize adjusts size to fit CURRENT strings
        tot_width = 0
        tot_height = 0
        widths = []
        for i in range(grid.GetNumberCols()):
            width = grid.GetColSize(i)
            widths.append(width)
            tot_width += width
        # Proportionally increase column widths until total width exceeds 400
        scale = max(400.0,tot_width)/tot_width
        tot_width = 0
        for i in range(grid.GetNumberCols()):
            grid.SetColSize(i,scale * widths[i])
            width = grid.GetColSize(i)
            tot_width += width
        for i in range(grid.GetNumberRows()):
            tot_height += grid.GetRowSize(i)
        # Find total height and widith of grid, and add 18 to each so that scroll bars do not appear
        return (tot_width+grid.GetRowLabelSize()+18,tot_height+grid.GetColLabelSize()+18)

    def doLayout(self,grid_size):
        self.GetSizer().SetItemMinSize(0,grid_size)
        self.SetAutoLayout(True)
        self.Layout()
        self.Fit()

    def fillValues(self):
        """ Fill the dialog form value fields with parameter values stored in self.paramValues """
        grid = self.parameterGrid
        row = 0     # Row in dialog form
        indx = 0    # Index into list of registers
        for param in self.details:
            regLoc,regType,reg,label,units,valueFmt,readable,writable = param
            val = self.paramValues[indx]
            if regType == 'mask':
                # For mask regType, the bits to be displayed are stored in the label field
                for bitfields in label:
                    bitmask,label,choices = bitfields
                    if choices:
                        value = bitmask & val
                        try:
                            which = self.vlist[reg][bitmask].index(value)
                            grid.SetCellValue(row,1,self.clist[reg][bitmask][which])
                        except:
                            grid.SetCellValue(row,1,"-- Invalid (%x) --" % int(value))
                        row += 1
            else:
                if regType == 'uint32':
                    if val == None:
                        grid.SetCellValue(row,1,"")
                    else:
                        grid.SetCellValue(row,1,valueFmt % (ctypes.c_uint32(val).value))
                if regType == 'uint16':
                    if val == None:
                        grid.SetCellValue(row,1,"")
                    else:
                        grid.SetCellValue(row,1,valueFmt % (ctypes.c_uint16(val).value))
                if regType == 'int32':
                    if val == None:
                        grid.SetCellValue(row,1,"")
                    else:
                        grid.SetCellValue(row,1,valueFmt % (ctypes.c_int32(val).value))
                if regType == 'int16':
                    if val == None:
                        grid.SetCellValue(row,1,"")
                    else:
                        grid.SetCellValue(row,1,valueFmt % (ctypes.c_int16(val).value))
                elif regType == 'float':
                    if val == None:
                        grid.SetCellValue(row,1,"")
                    else:
                        grid.SetCellValue(row,1,valueFmt % val)
                elif regType == 'choices':
                    try:
                        which = self.vlist[reg].index(val)
                        grid.SetCellValue(row,1,self.clist[reg][which])
                    except:
                        grid.SetCellValue(row,1,"-- Invalid (%d) --" % int(val))
                row += 1
            indx += 1

    def validateData(self):
        """ Validate data using information about the data type or the list of choices given.
            Return None if validation succeeds, or the row of the first invalid parameter """
        grid = self.parameterGrid
        newValues = []
        row = 0
        for param in self.details:
            regLoc,type,reg,label,units,format,readable,writable = param
            value = None
            if writable:
                if type == "mask":
                    mask = 0
                    value = 0
                    for bitfields in label:
                        valueAsText = grid.GetCellValue(row,1).strip()
                        bitmask,label,choices = bitfields
                        if choices:
                            mask |= bitmask
                            try:
                                value |= self.vlist[reg][bitmask][self.clist[reg][bitmask].index(valueAsText)]   # Check against list of valid choices in format
                            except:
                                return row
                            row += 1
                    value = (value,mask)
                else:
                    valueAsText = grid.GetCellValue(row,1).strip()
                    if valueAsText == None or (valueAsText == '' and type != 'choices'):
                        pass
                    elif type in ['int32', 'uint32', 'int16', 'uint16']:
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
            newValues.append(value)
        self.paramValues = newValues    # Only update stored values if all are valid
        return None

    def onCommit(self,e):
        """ Validate parameter values, write them to Das if valid, and destroy form """
        grid = self.parameterGrid
        grid.DisableCellEditControl()
        bad = self.validateData()
        if bad == None:
            self.writeParams()
            self.Destroy()
        else:   # Highlight the first invalid parameter value
            grid.SetGridCursor(bad,1)
            grid.SetFocus()

    def onApply(self,e):
        """ Validate parameter values, write them to DAS if valid, and re-read values
            leaving form open """
        grid = self.parameterGrid
        grid.DisableCellEditControl()
        bad = self.validateData()
        if bad == None:
            # Write to Das, then refresh values by reading from the Das
            self.writeParams()
            self.readParams()
        else:
            grid.SetGridCursor(bad,1)
            grid.SetFocus()

    def readParams(self):
        """ Read parameters to fill up form with current values"""
        regList = []
        badList = []
        for i,(regLoc,regType,reg,label,units,valueFmt,readable,writable) in enumerate(self.details):
            if readable:
                regList.append((regLoc,reg))
            else:
                badList.append(i)
        valueList = self.getRegisterValues(regList)
        for b in badList: valueList.insert(b,None)
        self.paramValues = valueList
        self.fillValues()

    def writeParams(self):
        """ Write parameters from current values in form"""
        # For efficiency, we get lists of register indices and values to write
        # Mask registers must be treated specially, since only some of the bits may need to be changed.  We need to read old
        #  values before modifying them.
        maskRegs = []
        for (regLoc,regType,reg,label,units,valueFmt,readable,writable),value in zip(self.details,self.paramValues):
            if writable and (value != None) and regType == "mask":
                maskRegs.append((regLoc,reg))
        bitValues = self.getRegisterValues(maskRegs)
        writeRegList = []
        writeValues = []
        for (regLoc,regType,reg,label,units,valueFmt,readable,writable),value in zip(self.details,self.paramValues):
            if writable and value != None:
                writeRegList.append((regLoc,reg))
                if regType == "mask":
                    val, mask = value
                    val |= bitValues.pop(0) & (~mask)
                    val &= 0xFFFFFFFFL
                    writeValues.append(val)
                else:
                    writeValues.append(value)
        self.putRegisterValues(writeRegList,writeValues)

    def onDiscard(self,e):
        """ Just destroy the form, discarding changes """
        self.Destroy()

    def onClose(self,e):
        """ Just destroy the form, discarding changes """
        self.Destroy()


if __name__ == "__main__":
    RDCNTRL_CMD_REGISTER = 123
    RDCNTRL_ETALON_DARK_READING1_REGISTER = 124
    RDCNTRL_RINGDOWN_CONTROL_REGISTER = 125
    RDCNTRL_REF_DARK_READING1_REGISTER = 126
    LSRICNTRL_DAC_SWEEP_INCR_REGISTER = 127

    RDCNTRL_Disable = 0
    RDCNTRL_EnableClt = 1
    RDCNTRL_EnableWt = 2
    RDCNTRL_EnterOsc = 3
    RDCNTRL_EnterManual = 4

    RDCNTRL_AutoRdwnEnableMask = 0x1
    RDCNTRL_CavityLengthTuningMask = 0x2
    RDCNTRL_WaveLengthTuningMask = 0x4
    RDCNTRL_ForceAbortMask = 0x8
    RDCNTRL_TunerUpSlopeEnableMask = 0x10
    RDCNTRL_TunerDownSlopeEnableMask = 0x20

    RDCNTRL_Disable = 0
    RDCNTRL_Enable  = 1

    myRegValues = { RDCNTRL_ETALON_DARK_READING1_REGISTER : 200,
                    RDCNTRL_RINGDOWN_CONTROL_REGISTER     : RDCNTRL_EnableClt,
                    RDCNTRL_REF_DARK_READING1_REGISTER    : 195,
                    LSRICNTRL_DAC_SWEEP_INCR_REGISTER     : 0.15
                }

    def myGetRegisterValues(regList):
        return [myRegValues[reg] for (regLoc,reg) in regList]

    def myPutRegisterValues(regList,values):
        global myRegValues
        print "Calling myPutRegisterValues"
        print regList
        print values
        for (regLoc,reg),value in zip(regList,values):
            myRegValues[reg] = value

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    parameterDialog = ParameterDialog(None, wx.ID_ANY, "")
    parameterDialog.getRegisterValues = myGetRegisterValues
    parameterDialog.putRegisterValues = myPutRegisterValues

    app.SetTopWindow(parameterDialog)

    p = []
    p.append(('dsp','choices',RDCNTRL_CMD_REGISTER,'Set ringdown mode',None,[(RDCNTRL_Disable,'Disable ringdowns'),(RDCNTRL_EnableClt,'Enable ringdowns with laser wavelength locking'),(RDCNTRL_EnableWt,'Enable ringdowns without laser wavelength locking'),(RDCNTRL_EnterOsc,'Enable oscilloscope mode'),(RDCNTRL_EnterManual,'Enter manual mode'),],0,1))
    p.append(('dsp','int',RDCNTRL_ETALON_DARK_READING1_REGISTER,'Etalon PD 1 dark reading','digU',"%d",1,0))
    bitfields = [(RDCNTRL_AutoRdwnEnableMask,"Ringdown sequencer",[(0,"Manual"),(RDCNTRL_AutoRdwnEnableMask,"Automatic")]),
                 (RDCNTRL_CavityLengthTuningMask,"Laser wavelength locking",[(0,"Disabled"),(RDCNTRL_CavityLengthTuningMask,"Enabled")]),
                 (RDCNTRL_WaveLengthTuningMask,"Wait for wavelength locking",[(0,"Enabled"),(RDCNTRL_WaveLengthTuningMask,"Bypass")]),
                 (RDCNTRL_ForceAbortMask,"Abort ringdown cycle",[(0,"Disabled"),(RDCNTRL_ForceAbortMask,"Abort")]),
                 (RDCNTRL_TunerUpSlopeEnableMask,"Allow ringdowns on positive slope",[(0,"No"),(RDCNTRL_TunerUpSlopeEnableMask,"Yes")]),
                 (RDCNTRL_TunerDownSlopeEnableMask,"Allow ringdowns on negative slope",[(0,"No"),(RDCNTRL_TunerDownSlopeEnableMask,"Yes")])]
    p.append(('dsp','mask',RDCNTRL_RINGDOWN_CONTROL_REGISTER,bitfields,None,None,1,1))
    p.append(('dsp','int',RDCNTRL_REF_DARK_READING1_REGISTER,'Ref PD 1 dark reading','digU',"%d",1,0))
    p.append(('dsp','float',LSRICNTRL_DAC_SWEEP_INCR_REGISTER,'Sweep increment','digU/sample',"%.1f",1,1))

    parameterDialog.initialize('Ringdown parameters',p)
    parameterDialog.readParams()
    parameterDialog.Show()
    app.MainLoop()
