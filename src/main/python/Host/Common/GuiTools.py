import wx

def normalizeBoolean(s):
    s = s.lower()
    if s in ("1","yes","true","on"): return True
    if s in ("0","no","false","off"): return False
    raise ValueError("Invalid boolean value: %s" % (s,))

def setItemFont(obj,fontTuple):
    font,fg,bg = fontTuple
    obj.SetFont(font)
    obj.SetForegroundColour(fg)
    obj.SetBackgroundColour(bg)

def getInnerStr(str):
    """
    This function is used to get around the problem that ConfigObj can't read '#' in
    any value assignment. To assign a HTML color code we have to use quotes to enclose
    the color value like '#85B24A'. When ConfigObj parses configuration file it returns
    "'#85B24A'" (when list_values option is False), and we need to get the inner sring.
    This is not needed if list_values optin is True in ConfigObj. But to be consistent
    we always set list_values as False and use this function as special case.
    """
    if ("'" in str) or ('"' in str):
        try:
            innerStr = eval(str)
            if type(innerStr) == type(''):
                return innerStr
        except:
            pass
    return str

class DataXferValidator(wx.PyValidator):
    def __init__(self,data,key,validator):
        wx.PyValidator.__init__(self)
        self.data = data
        self.key = key
        self.validator = validator

    def Clone(self):
        return DataXferValidator(self.data,self.key,self.validator)

    def Validate(self,win):
        ctrl = self.GetWindow()
        if isinstance(ctrl,wx.TextCtrl):
            text = ctrl.GetValue()
            if len(text)==0:
                wx.MessageBox("This field should not be empty","Error")
                ctrl.SetBackgroundColour("pink")
                ctrl.SetFocus()
                ctrl.Refresh()
                return False
        if self.validator is not None:
            return self.validator(ctrl,win)
        else:
            return True

    def TransferToWindow(self):
        ctrl = self.GetWindow()
        if isinstance(ctrl,wx.StaticText):
            ctrl.SetLabel(self.data.get(self.key,""))
        else:
            ctrl.SetValue(self.data.get(self.key,""))
        return True

    def TransferFromWindow(self):
        ctrl = self.GetWindow()
        if not isinstance(ctrl,wx.StaticText):
            self.data[self.key] = ctrl.GetValue()
        return True