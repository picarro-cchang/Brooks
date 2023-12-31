APP_NAME = "QuickGui"

import os
import sys
import wx
import time
import threading
from wx.lib.wordwrap import wordwrap
from Host.Common.GuiTools import *
from Host.Common import AppStatus
from Host.Common import CmdFIFO, Listener, TextListener
from Host.Common.SharedTypes import STATUS_PORT_INST_MANAGER, BROADCAST_PORT_IPV, RPC_PORT_DRIVER
from Host.Common.InstMgrInc import INSTMGR_STATUS_CAVITY_TEMP_LOCKED, INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED, \
                                   INSTMGR_STATUS_WARMING_UP, INSTMGR_STATUS_SYSTEM_ERROR, \
                                   INSTMGR_STATUS_PRESSURE_LOCKED, INSTMGR_STATUS_MEAS_ACTIVE
from Host.Common.EventManagerProxy import *
from Host.autogen import interface

EventManagerProxy_Init(APP_NAME)

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"):  #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)


class SysAlarmDialog(wx.Dialog):
    def __init__(self,
                 mainForm,
                 data,
                 parent,
                 id,
                 title,
                 fontDatabase,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        self.mainForm = mainForm
        # getFontFromIni = mainForm.getFontFromIni
        # setItemFont(self,self.mainForm.getFontFromIni('Dialogs'))
        setItemFont(self, fontDatabase.getFontFromIni('Dialogs'))
        self.data = data
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(hgap=5, vgap=5)
        label = wx.StaticText(self, -1, "Alarm name")
        # setItemFont(label,getFontFromIni('Dialogs'))
        setItemFont(label, fontDatabase.getFontFromIni('Dialogs'))

        sizer.Add(label, pos=(0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.name = wx.StaticText(parent=self, id=-1, size=(100, -1))
        self.name.SetValidator(DataXferValidator(data, "name", None))
        sizer.Add(self.name, pos=(0, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=5)
        self.instructions = wx.StaticText(self, -1, "")
        if data["name"] == "System Alarm":
            self.instructions.SetLabel(
                wordwrap(
                    "System alarm monitors the current instrument status, such as pressure, temperature, and measurement status",
                    300, wx.ClientDC(self)))
        elif data["name"] == "IPV Connectivity":
            self.instructions.SetLabel(
                wordwrap("IPV connectivity alarm monitors the connection between IPV program and Picarro Data Processing Center",
                         300, wx.ClientDC(self)))
        sizer.Add(self.instructions, pos=(1, 0), span=(1, 2), flag=wx.ALL, border=5)
        #self.enabled = wx.CheckBox(self,-1,"Enable alarm")
        #self.enabled.SetValidator(DataXferValidator(data,"enabled",None))
        #sizer.Add(self.enabled, pos=(2,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, border=5)

        self.vsizer.Add(sizer)
        #line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        #self.vsizer.Add(line, 0, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        setItemFont(btn, fontDatabase.getFontFromIni('DialogButtons'))
        btn.SetDefault()
        btnsizer.AddButton(btn)

        #btn = wx.Button(self, wx.ID_CANCEL)
        #setItemFont(btn,getFontFromIni('DialogButtons'))
        #btnsizer.AddButton(btn)

        btnsizer.Realize()

        self.vsizer.Add(btnsizer, 0, flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALL, border=5)
        self.SetSizer(self.vsizer)
        self.vsizer.Fit(self)


class SysAlarmViewListCtrl(wx.ListCtrl):
    """ListCtrl to display alarm status
    attrib is a list of wx.ListItemAttr objects for the disabled and enabled alarm text
    DataSource must be the AlarmInterface object which reads the alarm status
    """
    def __init__(self,
                 parent,
                 id,
                 attrib,
                 DataSource=None,
                 fontDatabase=None,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 numAlarms=2):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_NO_HEADER | wx.NO_BORDER)
        self.parent = parent
        self.ilEventIcons = wx.ImageList(32, 32)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        thisDir = os.path.dirname(os.path.abspath(__file__))
        self.IconAlarmOff = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidOff_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmGreen = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidGreen_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmYellow = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidYellow_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmRed = myIL.Add(wx.Bitmap(thisDir + '/LED_SolidRed_32x32.png', wx.BITMAP_TYPE_ICO))
        self.currentAlarmColor = ["RED", "RED"]
        self._DataSource = DataSource
        self.dataStore = None
        self.fontDatabase = fontDatabase
        self.InsertColumn(0, "Icon", width=40)
        sx, sy = self.GetSize()
        self.InsertColumn(1, "Name", width=sx - 40 - 17)
        self.attrib = attrib
        self.SetItemCount(numAlarms)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.tipWindow = None
        self.tipItem = None
        self.driverRpc = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, ClientName=APP_NAME)

    def SetMainForm(self, mainForm):
        self.mainForm = mainForm

    def OnMouseDown(self, evt):
        pass

    def OnLeftDown(self, evt):
        pos = evt.GetPositionTuple()
        item, flags = self.HitTest(pos)
        if self.tipWindow:
            self.tipWindow.Close()
        name, enabled = self._DataSource.alarmData[item]
        d = dict(name=name, enabled=enabled)
        dialog = SysAlarmDialog(self.mainForm, d, None, -1, "Alarm Description", self.fontDatabase)
        retCode = dialog.ShowModal()
        dialog.Destroy()
        if retCode == wx.ID_OK:
            self._DataSource.setAlarm(item, d["enabled"])

    def OnMouseMotion(self, evt):
        pos = evt.GetPositionTuple()
        item, flags = self.HitTest(pos)
        if item >= 0:
            if self.tipWindow:
                self.tipWindow.Close()
            rect = self.GetItemRect(item)
            left, top = self.ClientToScreenXY(rect.x, rect.y)
            right, bottom = self.ClientToScreenXY(rect.GetRight(), rect.GetBottom())
            rect = wx.Rect(left, top, right - left + 1, bottom - top + 1)
            goodStatus, descr = self._DataSource.getStatus(item)
            self.tipWindow = wx.TipWindow(self, "%s" % (descr, ), maxLength=1000, rectBound=rect)
        evt.Skip()

    def OnGetItemText(self, item, col):
        if col == 1:
            return self._DataSource.alarmData[item][0]
        else:
            return ""

    def OnGetItemAttr(self, item):
        # Use appropriate attributes for enabled and disabled items
        if self._DataSource.alarmData[item][1]:
            return self.attrib[1]
        else:
            return self.attrib[0]

    def OnGetItemImage(self, item):
        alarmColor = self.IconAlarmRed
        goodStatus, descr = self._DataSource.getStatus(item)
        enabled = self._DataSource.alarmData[item][1]
        if goodStatus == 3:  # green condition
            alarmColor = self.IconAlarmGreen
            self.currentAlarmColor[item] = "GREEN"
        elif goodStatus == 2:  # blinking yellow
            if "YELLOW" in self.currentAlarmColor[item]:
                alarmColor = self.IconAlarmOff
                self.currentAlarmColor[item] = "OFF"
            else:
                alarmColor = self.IconAlarmYellow
                self.currentAlarmColor[item] = "YELLOW"
        elif goodStatus == 1:  # solid yellow
            alarmColor = self.IconAlarmYellow
            self.currentAlarmColor[item] = "YELLOW"
        elif not enabled:
            alarmColor = self.IconAlarmOff
            self.currentAlarmColor[item] = "OFF"
        else:
            alarmColor = self.IconAlarmRed
            self.currentAlarmColor[item] = "RED"

        if item == 0:
            realLEDState = self.driverRpc.rdFPGA("FPGA_KERNEL", "KERNEL_STATUS_LED")
            if self.currentAlarmColor[item] == "GREEN":
                realLEDState |= 1 << interface.KERNEL_STATUS_LED_GREEN_B
                realLEDState &= ~(1 << interface.KERNEL_STATUS_LED_RED_B)
            elif self.currentAlarmColor[item] == "YELLOW":
                realLEDState |= 1 << interface.KERNEL_STATUS_LED_GREEN_B
                realLEDState |= 1 << interface.KERNEL_STATUS_LED_RED_B
            elif self.currentAlarmColor[item] == "RED":
                realLEDState |= 1 << interface.KERNEL_STATUS_LED_RED_B
                realLEDState &= ~(1 << interface.KERNEL_STATUS_LED_GREEN_B)
            else:
                realLEDState &= ~(1 << interface.KERNEL_STATUS_LED_GREEN_B)
                realLEDState &= ~(1 << interface.KERNEL_STATUS_LED_RED_B)
            self.driverRpc.wrFPGA("FPGA_KERNEL", "KERNEL_STATUS_LED", realLEDState)

        return alarmColor

    def Defocus(self):
        """
        GTK version of ListCtrl automatically sets the focus rectangle on
        a list item even if the focus is on an entirely different widget.
        This will remove the focus state.
        Note that this needs to be called after every screen redraw.
        """
        self.SetItemState(self.GetFocusedItem(), 0, wx.LIST_STATE_FOCUSED)

    def RefreshList(self):
        self.RefreshItems(0, self.GetItemCount() - 1)
        self.Defocus()


class SysAlarmInterface(object):
    """Interface to the alarm system RPC and status ports"""
    def __init__(self, ledBlinkTime=0):
        self.instMgrStatusListener = Listener.Listener(None,
                                                       STATUS_PORT_INST_MANAGER,
                                                       AppStatus.STREAM_Status,
                                                       self._InstMgrStatusFilter,
                                                       retry=True,
                                                       name="System Alarm Instrument Manager listener")
        self.ipvListener = TextListener.TextListener(None,
                                                     BROADCAST_PORT_IPV,
                                                     self._IPVStatusFilter,
                                                     retry=True,
                                                     name="System Alarm IPV listener")

        self.alarmData = [["System Alarm", True], ["IPV Connectivity", False]]
        self.latestInstMgrStatus = -1
        self.latestIPVStatus = "-1,%s" % (time.time() + 120)
        self.ipvStatusDict = {
            0: "IPV Connectivity Status: Failed",
            1: "IPV Connectivity Status: Good",
            -1: "IPV Connectivity Status: Unknown",
            100: "IPV Disabled"
        }
        self.lastIPVStatus = None

        # After the initial warm up the system may be unstable and the warm/hot
        # box may loose the temperature lock after achieving its initial lock.
        # We this mostly when the system is already warm and restarted.  In
        # this case the temperature PID can take awhile to settle about the
        # set temperature and the system may lock/unlock several times as the
        # temperature oscillations settle.
        #
        # To avoid the status LED from switching repeated from green to red and
        # back, we can make the LED blink yellow (the warmup indication) for a
        # set extended period until we are sure to be past any PID caused
        # oscillations.
        #
        # To enable this feature set ledBlinkTime to anything greater than
        # zero.  The units are seconds.  This value is set in QuickGui.ini
        # in the section AlarmBox | LedBlinkTime.  This key is optional. If not
        # found the ledBlinkTime is 0 and the LED will blink yellow until the
        # first time measurement status is achieved.
        #
        self._makeLedBlink = True
        self.OneShotTimer = threading.Timer(ledBlinkTime, self._ledBlinkTimer)
        self.OneShotTimer.start()

    def _ledBlinkTimer(self):
        self._makeLedBlink = False

    def _InstMgrStatusFilter(self, obj):
        """Updates the local (latest) copy of the instrument manager status bits."""
        self.latestInstMgrStatus = obj.status

    def _IPVStatusFilter(self, obj):
        """Updates the local (latest) copy of the IPV status bits."""
        self.latestIPVStatus = obj

    def setAlarm(self, index, enable):
        """Set alarm enable and threshold by making a non-blocking RPC call to the alarm system"""
        self.alarmData[index][1] = enable

    def getStatus(self, index):
        # Big hack here (RSF 04/16/2017)
        #
        # Code used to return 'good' as a bool.
        # Now we need to go to a 5 state system which is
        #
        # Off - no reading
        # Green - all ok
        # Yellow - warning or maintenance needed soon
        # Blinking yellow - all ok but we are warming up or in service/calibration mode
        # Red - error condition, data bad or not reporting
        #
        # 0 - red
        # 1 - yellow
        # 2 - blinking yellow
        # 3 - green
        # 4 - off
        good = 0  # default to red
        if index == 0:
            descr = "System Status: Good"
            pressureLocked = self.latestInstMgrStatus & INSTMGR_STATUS_PRESSURE_LOCKED
            cavityTempLocked = self.latestInstMgrStatus & INSTMGR_STATUS_CAVITY_TEMP_LOCKED
            warmboxTempLocked = self.latestInstMgrStatus & INSTMGR_STATUS_WARM_CHAMBER_TEMP_LOCKED
            measActive = self.latestInstMgrStatus & INSTMGR_STATUS_MEAS_ACTIVE
            warmingUp = self.latestInstMgrStatus & INSTMGR_STATUS_WARMING_UP
            systemError = self.latestInstMgrStatus & INSTMGR_STATUS_SYSTEM_ERROR
            if pressureLocked and cavityTempLocked and warmboxTempLocked and measActive and (not warmingUp) and (
                    not systemError) and (not self._makeLedBlink):
                good = 3  # green
            if good != 3:
                descr = "System Status:"
                if warmingUp or self._makeLedBlink:
                    descr += "\n* Warming Up"
                    good = 2  # blinking yellow
                if systemError:
                    descr += "\n* System Error"
                if not pressureLocked:
                    descr += "\n* Pressure Unlocked"
                if not cavityTempLocked:
                    descr += "\n* Cavity Temp Unlocked"
                if not warmboxTempLocked:
                    descr += "\n* Warm Box Temp Unlocked"
                if not measActive:
                    descr += "\n* Measurement Not Active"
                    good = 2
            return good, descr
        elif index == 1:
            ipvStatus, timestamp = self.latestIPVStatus.split(",")
            ipvStatus = int(ipvStatus)
            timestamp = float(timestamp)
            if time.time() - timestamp > 120:
                self.setAlarm(1, False)
                ipvStatus = 100
                goodStatus = True
            else:
                self.setAlarm(1, True)
                goodStatus = True
                if ipvStatus == -1:
                    self.setAlarm(1, False)
                elif ipvStatus == 0:
                    goodStatus = False
            if ipvStatus != self.lastIPVStatus:
                Log("New IPV status: %s" % self.ipvStatusDict[ipvStatus])
                self.lastIPVStatus = ipvStatus
            return goodStatus, self.ipvStatusDict[ipvStatus]
