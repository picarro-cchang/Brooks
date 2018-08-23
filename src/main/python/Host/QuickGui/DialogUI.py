import wx
from wx.lib.wordwrap import wordwrap
from Host.Common.GuiTools import setItemFont, DataXferValidator

class OKDialog(wx.Dialog):
    def __init__(self,mainForm,aboutText,parent,id,title,fontDatabase,pos=wx.DefaultPosition,size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE, boldText = None):
        super(OKDialog, self).__init__(parent,id,title,pos,size,style)
        self.okButton = wx.Button(self, wx.ID_OK)
        self.aboutText = wx.StaticText(self,-1,aboutText)
        if boldText:
            boldFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            self.boldText = wx.StaticText(self,-1,boldText)
            self.boldText.SetFont(boldFont)
        else:
            self.boldText = None
        self.mainForm = mainForm
        setItemFont(self,fontDatabase.getFontFromIni("Dialogs"))
        setItemFont(self.okButton,fontDatabase.getFontFromIni("DialogButtons"))
        self.__do_layout()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ShutdownDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        if self.boldText:
            sizer_1.Add((-1,10))
            sizer_1.Add(self.boldText, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=5)
        sizer_1.Add(self.aboutText, flag=wx.ALL, border=5)
        #sizer_2.AddButton(self.okButton)
        #sizer_2.Realize()
        sizer_2.Add((20,20),1)
        sizer_2.Add(self.okButton)
        sizer_2.Add((20,20),1)
        sizer_1.Add(sizer_2, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

class ShutdownDialog(wx.Dialog):
    def __init__(self, mainForm, *args, **kwds):
        # begin wxGlade: ShutdownDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        super(ShutdownDialog, self).__init__(*args, **kwds)
        self.selectShutdownType = wx.RadioBox(self, -1, "Select shutdown method",
            choices=["Turn Off Analyzer and Prepare For Shipping", "Turn Off Analyzer in Current State", "Stop Analyzer Software Only"], majorDimension=3,
            style=wx.RA_SPECIFY_ROWS)
        self.okButton = wx.Button(self, wx.ID_OK)
        self.cancelButton = wx.Button(self, wx.ID_CANCEL)
        self.fontDatabase = fontDatabase
        self.mainForm = mainForm
        self.__set_properties()
        self.__do_layout()

        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: ShutdownDialog.__set_properties
        self.SetTitle("Shutdown Instrument")
        self.selectShutdownType.SetSelection(0)
        setItemFont(self,self.fontDatabase.getFontFromIni("Dialogs"))
        setItemFont(self.okButton,self.fontDatabase.getFontFromIni("DialogButtons"))
        setItemFont(self.cancelButton,self.fontDatabase.getFontFromIni("DialogButtons"))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ShutdownDialog.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.StdDialogButtonSizer()
        sizer_1.Add(self.selectShutdownType, 1, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
        sizer_2.AddButton(self.okButton)
        sizer_2.AddButton(self.cancelButton)
        sizer_2.Realize()
        sizer_1.Add(sizer_2, 0, wx.ALL|wx.EXPAND, 10)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

    def getShutdownType(self):
        return self.selectShutdownType.GetSelection()


class AlarmDialog(wx.Dialog):
    modeInstructions = {"Higher":\
                        "Alarm is set when value is above Alarm threshold 1. It is reset when value falls below Clear threshold 1.",
                        "Lower":\
                        "Alarm is set when value is below Alarm threshold 1. It is reset when value rises above Clear threshold 1.",
                        "Inside":\
                        "Alarm is set when value is below Alarm threshold 1 and above Alarm threshold 2.\nIt is reset when value rises above Clear threshold 1 or falls below Clear threshold 2.",
                        "Outside":\
                        "Alarm is set when value is above Alarm threshold 1 or below Alarm threshold 2.\nIt is reset when value falls below Clear threshold 1 or rises above Clear threshold 2."}
    def __init__(self,mainForm,data,parent,id,title,fontDatabase,pos=wx.DefaultPosition,size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE):
        super(AlarmDialog, self).__init__(parent,id,title,pos,size,style)

        self.mainForm = mainForm
        setItemFont(self,fontDatabase.getFontFromIni('Dialogs'))
        self.data = data
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(hgap=5,vgap=5)
        label = wx.StaticText(self, -1, "Alarm name")
        setItemFont(label,fontDatabase.getFontFromIni('Dialogs'))

        sizer.Add(label, pos = (0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)
        self.name = wx.StaticText(parent=self,id=-1,size=(100,-1))
        self.name.SetValidator(DataXferValidator(data,"name",None))
        sizer.Add(self.name, pos = (0,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)
        self.instructions = wx.StaticText(self,-1,"")
        label = wx.StaticText(self, -1, "Alarm mode")
        sizer.Add(label, pos = (1,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)
        self.mode = wx.ComboBox(parent=self,id=-1,size=(125,-1),style=wx.CB_READONLY,
                            choices=["Higher","Lower","Inside","Outside"])
        #self.mode = wx.StaticText(parent=self,id=-1,size=(100,-1))
        self.mode.SetValidator(DataXferValidator(data,"mode",None))
        sizer.Add(self.mode, pos = (1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border = 5)
        self.instructions = wx.StaticText(self,-1,"")
        sizer.Add(self.instructions, pos=(2,0), span=(1,2), flag=wx.ALL, border=5)

        label = wx.StaticText(self, -1, "Alarm threshold 1")
        sizer.Add(label, pos=(3,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        self.alarm1Edit = wx.TextCtrl(self, -1, "0.0", size=(125, -1))
        setItemFont(self.alarm1Edit,fontDatabase.getFontFromIni('DialogTextBoxes'))
        self.alarm1Edit.SetValidator(DataXferValidator(data,"alarm1",self.validate))
        sizer.Add(self.alarm1Edit, pos=(3,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        label = wx.StaticText(self, -1, "Clear threshold 1")
        sizer.Add(label, pos=(4,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        self.clear1Edit = wx.TextCtrl(self, -1, "0.0", size=(125, -1))
        setItemFont(self.clear1Edit,fontDatabase.getFontFromIni('DialogTextBoxes'))
        self.clear1Edit.SetValidator(DataXferValidator(data,"clear1",self.validate))
        sizer.Add(self.clear1Edit, pos=(4,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        label = wx.StaticText(self, -1, "Alarm threshold 2")
        sizer.Add(label, pos=(5,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        self.alarm2Edit = wx.TextCtrl(self, -1, "0.0", size=(125, -1))
        setItemFont(self.alarm2Edit,fontDatabase.getFontFromIni('DialogTextBoxes'))
        self.alarm2Edit.SetValidator(DataXferValidator(data,"alarm2",self.validate))
        sizer.Add(self.alarm2Edit, pos=(5,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        label = wx.StaticText(self, -1, "Clear threshold 2")
        sizer.Add(label, pos=(6,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        self.clear2Edit = wx.TextCtrl(self, -1, "0.0", size=(125, -1))
        setItemFont(self.clear2Edit,fontDatabase.getFontFromIni('DialogTextBoxes'))
        self.clear2Edit.SetValidator(DataXferValidator(data,"clear2",self.validate))
        sizer.Add(self.clear2Edit, pos=(6,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL, border=5)
        self.enabled = wx.CheckBox(self,-1,"Enable alarm")
        self.enabled.SetValidator(DataXferValidator(data,"enabled",None))
        sizer.Add(self.enabled, pos=(7,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, border=5)

        self.vsizer.Add(sizer)
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.vsizer.Add(line, 0, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        setItemFont(btn,fontDatabase.getFontFromIni('DialogButtons'))
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        setItemFont(btn,fontDatabase.getFontFromIni('DialogButtons'))
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        self.vsizer.Add(btnsizer, 0, flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, border=5)
        self.SetSizer(self.vsizer)
        self.selectMode(data["mode"])
        self.Bind(wx.EVT_COMBOBOX, self.onModeComboBox, self.mode)

    def setDialogValues(self,name,mode,enabled,alarm1,clear1,alarm2,clear2):
        self.name.SetLabel(name)
        self.alarm1Edit.SetValue("%.2f" % alarm1)
        self.clear1Edit.SetValue("%.2f" % clear1)
        self.alarm2Edit.SetValue("%.2f" % alarm2)
        self.clear2Edit.SetValue("%.2f" % clear2)
        self.enabled.SetValue(enabled)
        self.mode.SetLabel(mode)
        self.selectMode(mode)

    def onModeComboBox(self,evt):
        self.selectMode(evt.GetEventObject().GetValue())

    def selectMode(self,mode):
        self.mode.SetValidator(DataXferValidator(self.data,"mode",None))
        self.data["mode"] = mode
        self.instructions.SetLabel(wordwrap(self.modeInstructions[mode],300, wx.ClientDC(self)))
        if mode in ["Higher","Lower"]:
            self.alarm2Edit.Enable(False)
            self.clear2Edit.Enable(False)
        if mode in ["Inside","Outside"]:
            self.alarm2Edit.Enable(True)
            self.clear2Edit.Enable(True)
        self.SendSizeEvent()
        self.vsizer.Fit(self)

    def validate(self,ctrl,parent):
        try:
            v = float(ctrl.GetValue())
        except ValueError:
            wx.MessageBox("This field does not contain number","Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        try:
            alarm1 = float(self.alarm1Edit.GetValue())
            alarm2 = float(self.alarm2Edit.GetValue())
            clear1 = float(self.clear1Edit.GetValue())
            clear2 = float(self.clear2Edit.GetValue())
        except ValueError:
            return True # This will be caught later
        mode = self.data["mode"]
        if mode in ["Higher","Outside"]:
            if alarm1<clear1:
                wx.MessageBox("In %s mode, Alarm threshold 1 must be above Clear threshold 1" % mode,"Error")
                return False
        if mode in ["Lower","Inside"]:
            if alarm1>clear1:
                wx.MessageBox("In %s mode, Alarm threshold 1 must be below Clear threshold 1" % mode,"Error")
                return False
        if mode in ["Outside"]:
            if alarm2>clear2:
                wx.MessageBox("In %s mode, Alarm threshold 2 must be below Clear threshold 2" % mode,"Error")
                return False
            if alarm1<clear2:
                wx.MessageBox("In %s mode, Alarm threshold 1 must be above Clear threshold 2" % mode,"Error")
                return False
            if alarm2>clear1:
                wx.MessageBox("In %s mode, Alarm threshold 2 must be below Clear threshold 1" % mode,"Error")
                return False
        if mode in ["Inside"]:
            if alarm2<clear2:
                wx.MessageBox("In %s mode, Alarm threshold 2 must be above Clear threshold 2" % mode,"Error")
                return False
        if mode in ["Inside", "Outside"]:
            if alarm1<alarm2:
                wx.MessageBox("In %s mode, Alarm threshold 1 must be above Alarm threshold 2" % mode,"Error")
                return False
        return True


class LoginDialog(wx.Dialog):
    def __init__(self, parent, title="Login", user="", msg=""):
        super(LoginDialog, self).__init__(parent, title = title)
        self.user = wx.TextCtrl(self, -1, user)
        self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.msg = wx.TextCtrl(self, -1, msg, size=(-1, 50),
            style=wx.TE_READONLY | wx.BORDER_NONE | wx.TE_MULTILINE)

        self.__DoLayout()
        self.SetInitialSize((300, 230))
        self.user.SetFocus()

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        fieldSz = wx.FlexGridSizer(2,2,5,8)
        fieldSz.AddGrowableCol(1,1)
        userLbl = wx.StaticText(self, label= "Username:")
        fieldSz.Add(userLbl, 0, wx.ALIGN_CENTER_VERTICAL)
        fieldSz.Add(self.user, 1, wx.EXPAND)
        passLbl = wx.StaticText(self, label= "Password:")
        fieldSz.Add(passLbl, 0, wx.ALIGN_CENTER_VERTICAL)
        fieldSz.Add(self.password, 1, wx.EXPAND)

        sizer.Add((10,10))
        sizer.Add(fieldSz, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.msg, 1, wx.ALL|wx.EXPAND, 5)
        btnSz = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        sizer.Add(btnSz, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 5)

        self.Sizer = sizer

    def getInput(self):
        return self.user.Value, self.password.Value


class ChangePasswordDialog(wx.Dialog):
    def __init__(self, parent, title="Change Password", msg=""):
        super(ChangePasswordDialog, self).__init__(parent, title = title)

        self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.password2 = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.msg = wx.TextCtrl(self, -1, msg, size=(-1, 50),
            style=wx.TE_READONLY | wx.BORDER_NONE | wx.TE_MULTILINE)

        self.__DoLayout()
        self.SetInitialSize((350, 200))
        self.password.SetFocus()

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        fieldSz = wx.FlexGridSizer(2,2,5,8)
        fieldSz.AddGrowableCol(1,1)
        pwdLbl = wx.StaticText(self, label= "New Password:")
        fieldSz.Add(pwdLbl, 0, wx.ALIGN_CENTER_VERTICAL)
        fieldSz.Add(self.password, 1, wx.EXPAND)
        pwd2Lbl = wx.StaticText(self, label= "Confirm Password:")
        fieldSz.Add(pwd2Lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        fieldSz.Add(self.password2, 1, wx.EXPAND)

        sizer.Add((10,10))
        sizer.Add(fieldSz, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.msg, 1, wx.ALL|wx.EXPAND, 5)
        btnSz = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        sizer.Add(btnSz, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 5)

        self.Sizer = sizer

    def getInput(self):
        return self.password.Value, self.password2.Value
