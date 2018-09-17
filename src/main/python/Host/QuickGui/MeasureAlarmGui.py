import wx
import os
import datetime
import Host.QuickGui.DialogUI as Dialog

class AlarmViewListCtrl(wx.ListCtrl):
    """
    ListCtrl to display gas concentrations (and other measureable properties) alarm status.
    attrib is a list of wx.ListItemAttr objects for the disabled and enabled alarm text.
    DataSource must be the AlarmInterface object which reads the alarm status.

    Note that the "Status" alarm is controlled SysAlarmViewListCtrl in SysAlarmGui.py.
    """
    def __init__(self, parent, mainForm, id, attrib, DataStore=None, DataSource=None, fontDatabase=None,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, numAlarms=4,sysAlarmInterface=None):
        wx.ListCtrl.__init__(self, parent, id, pos, size,
                             style = wx.LC_REPORT
                             | wx.LC_VIRTUAL
                             | wx.LC_NO_HEADER
                             | wx.NO_BORDER
                         )
        self.parent = parent # ptr to subpanel containing this widget
        self.mainForm = mainForm  # pointer to main GUI screen, need for GUI look-n-feel attributes
        self.attrib = attrib
        self.dataStore = DataStore
        self._DataSource = DataSource
        self._sysAlarmInterface = sysAlarmInterface
        self._fontDatabase = fontDatabase
        self.tipWindow = None
        self.tipItem = None
        self.dummyCounter = 0

        self.appPath = os.path.dirname(os.path.abspath(__file__))


        # Create Alarm LED icons. Colors
        self.ilEventIcons = wx.ImageList(32, 32)
        self.SetImageList(self.ilEventIcons, wx.IMAGE_LIST_SMALL)
        myIL = self.GetImageList(wx.IMAGE_LIST_SMALL)
        self.IconAlarmOff  = myIL.Add(wx.Bitmap(self.appPath + '/LED_SolidOff_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmGreen  = myIL.Add(wx.Bitmap(self.appPath + '/LED_SolidGreen_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmYellow  = myIL.Add(wx.Bitmap(self.appPath + '/LED_SolidYellow_32x32.png', wx.BITMAP_TYPE_ICO))
        self.IconAlarmRed    = myIL.Add(wx.Bitmap(self.appPath + '/LED_SolidRed_32x32.png', wx.BITMAP_TYPE_ICO))

        # Set column dimensions, must subtract off width needed for scrollbars (17)
        self.InsertColumn(0,"Icon",width=40)
        sx,sy = self.GetSize()
        # self.InsertColumn(1, "Name", width=sx-40-17)
        self.InsertColumn(1, "Name", width=sx+20) # Works better with longer alarm label text

        self.alarmNames = []
        for i in range(numAlarms):
            self.alarmNames.append("Alarm %d" % (i+1))
        self.SetItemCount(numAlarms)

        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftDown)
        self.Bind(wx.EVT_MOTION,self.OnMouseMotion)

    def DisableMouseButton(self, disable):
        # In the QuickGui we use the user login level to enable/disable access to the alarm settings menu.
        # By default this menu cannot be accessed.
        if disable:
            self.Unbind(wx.EVT_LEFT_DOWN)
        else:
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        return

    def OnLeftDown(self,evt):
        """
        If left click a concentration alarm, display a dialog that allows the user to change alarm set points.
        :param evt:
        :return:
        """
        #
        # The test for "Operating Range" is a hack.
        # A request is to throw an alarm if the gas exceeds the high concentration limit as set in the
        # product spec.  This is a fixed number not adjustable by the customer.  As such we want to
        # prevent the user from accessing the alarm threshold dialog.  Alarms of this type have a name
        # of the form "HF Operating Range".  If we find "Operating Range" we block the alarm setting
        # dialog.
        #
        # EDIT: 20180409
        # The phrase "Operating Range" has been changed to "Measuring Range" on SI units so now we just
        # look for "Range".
        #
        pos = evt.GetPositionTuple()
        item,flags = self.HitTest(pos)
        if self.tipWindow and self.tipWindow.IsShown():
            self.tipWindow.Close()
        if self._DataSource.alarmData:
            name,mode,enabled,alarm1,clear1,alarm2,clear2 = self._DataSource.alarmData[item]
            if "Range" not in name:
                alarm1 = "%.2f" % alarm1
                alarm2 = "%.2f" % alarm2
                clear1 = "%.2f" % clear1
                clear2 = "%.2f" % clear2
                d = dict(name=name,mode=mode,enabled=enabled,alarm1=alarm1,clear1=clear1,
                            alarm2=alarm2,clear2=clear2)
                dialog = Dialog.AlarmDialog(self.mainForm,d,None,-1,"Setting alarm %d" % (item+1,), self._fontDatabase)
                retCode = dialog.ShowModal()
                dialog.Destroy()
                if retCode == wx.ID_OK:
                    self._DataSource.setAlarm(item+1,d["enabled"],d["mode"],
                                              float(d["alarm1"]),float(d["clear1"]),
                                              float(d["alarm2"]),float(d["clear2"]))
        return

    def OnMouseMotion(self,evt):
        """
        When mouse over a concentration alarm, show the set points in a tooltip.
        :param evt:
        :return:
        """
        pos = evt.GetPositionTuple()
        item,flags = self.HitTest(pos)
        if item>=0:
            if self.tipWindow and self.tipWindow.IsShown():
                self.tipWindow.Close()
            rect = self.GetItemRect(item)
            left, top = self.ClientToScreenXY(rect.x, rect.y)
            right, bottom = self.ClientToScreenXY(rect.GetRight(), rect.GetBottom())
            rect = wx.Rect(left, top, right - left + 1, bottom - top + 1)
            if self._DataSource.alarmData:
                name,mode,enabled,alarm1,clear1,alarm2,clear2 = self._DataSource.alarmData[item]
                if mode == "Higher":
                    desc = "Alarm if > %.2f, Cleared when < %.2f" % (alarm1, clear1)
                elif mode == "Lower":
                    desc = "Alarm if < %.2f, Cleared when > %.2f" % (alarm1, clear1)
                elif mode == "Outside":
                    desc = "Alarm if < %.2f or > %.2f, Cleared when > %.2f and < %.2f" % \
                         (alarm2, alarm1, clear2, clear1)
                elif mode == "Inside":
                    desc = "Alarm if > %.2f and < %.2f, Cleared when < %.2f or > %.2f" % \
                         (alarm2, alarm1, clear2, clear1)
                self.tipWindow = wx.TipWindow(self,"%s" % (desc,),maxLength=1000,rectBound=rect)
        evt.Skip()
        return

    def OnGetItemText(self,item,col):
        """
        Get alarm human readable label.
        :param item:
        :param col:
        :return:
        """
        rtn = ""
        if col==1 and self._DataSource.alarmData:
            rtn = self._DataSource.alarmData[item][0]
        return rtn

    def OnGetItemAttr(self,item):
        # Use appropriate attributes for enabled and disabled items
        if self._DataSource.alarmData and self._DataSource.alarmData[item][2]:
            return self.attrib[1]
        else:
            return self.attrib[0]

    def OnGetItemImage(self, item):
        """
        When the list is refreshed with RefreshList() (are we sure?) it comes here
        to figure out what LED light to display.

        EDIT:
        Now we track the status of the system alarm to see if it is blinking. If so
        this indicates we are in a transition state like warming up, pressure or
        temperature unlocked, service mode etc.  If the system led is blinking turn
        off the gas concentration led.
        When the system alarm led is green (return code 3) all systems are good
        and the gas measurment is considered valid.
        """
        alarmColor = self.IconAlarmRed
        status = int(self.dataStore.alarmStatus) & (1 << item)
        enabled = (self._DataSource.alarmData and self._DataSource.alarmData[item][2])
        if not enabled:
            alarmColor = self.IconAlarmOff
        elif self._sysAlarmInterface.getStatus(0)[0] != 3:
            alarmColor = self.IconAlarmOff
        elif status == 0:
            alarmColor = self.IconAlarmGreen
        else:
            alarmColor = self.IconAlarmRed
        return alarmColor

    def Defocus(self):
        """
        GTK version of ListCtrl automatically sets the focus rectangle on
        a list item even if the focus is on an entirely different widget.
        This will remove the focus state.
        Note that this needs to be called after every screen redraw.
        """
        self.SetItemState(self.GetFocusedItem(), 0, wx.LIST_STATE_FOCUSED)
        return

    def RefreshList(self):
        self.RefreshItems(0,self.GetItemCount()-1)
        self.Defocus()
        return