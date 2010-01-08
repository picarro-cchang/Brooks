# File Name: DasUpgradeGui.py
# Purpose: This module is responsible for the GUI for the upgrader
#
# File History:
# 06-05-02 ytsai   Created file
# 06-05-29 ytsai   Added version to download
# 06-08-08 ytsai   Added password for upgrade
# 06-08-15 ytsai   Enable upgrade page after password retry succeeds.
# 07-02-14 sze     Added wx.FutureCall statements for wxPython version >= 2.8, so that GUI displays
#                   correctly during downloading
# 08-01-15 sze     Added support for programming Cypress FX2 USB code, tidied up indentation and
#                   organization of UpgradeXXXPage classes
import sys
import os
import glob
import wx
import wx.wizard as wiz
from   wizardhelper  import WizardTitledLogoPage
from   time import sleep

from   DasUpgrade    import DasUpgrade

_IMAGES_DIRECTORY = "./Images/"
_MCU_PAGE         = 0
_DSP_PAGE         = 1
_FPGA_PAGE        = 2
_USB_PAGE         = 3

_PROMPT_PASSWORD  = True
_UpgradePassword = 'picarro'

def _PrintStatus( status, newText ):
    last = status.GetLastPosition()
    status.SetInsertionPoint(last)
    status.WriteText(newText + "\n")
    wx.Yield()
    print newText

class UpgradeDasPage(WizardTitledLogoPage):
    def __init__(self, parent, title, version ):

        WizardTitledLogoPage.__init__(self, parent, title)

        self.version = version

        self.text1 = wx.StaticText( self, -1 )
        self.sizer.Add( self.text1, 0, wx.EXPAND | wx.ALL, 5  )

        self.status = wx.TextCtrl(self, -1, "", size=(180, 88), style=wx.TE_MULTILINE|wx.TE_READONLY )
        self.sizer.Add( self.status, 0, wx.EXPAND | wx.ALL, 5 )

        self.gauge = wx.Gauge(self, -1, 50, (510, 250), (450, 30))
        self.gauge.SetBezelFace(3)
        self.gauge.SetShadowWidth(3)
        self.sizer.Add( self.gauge, 0, wx.ALIGN_BOTTOM | wx.EXPAND | wx.ALL, 5 )

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnWizPageChanged)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnWizPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnWizCancel)

        self.Running = False

    def OnWizPageChanged(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
            return;

        if self.Running == True:
            return
        page = evt.GetPage()

        self.Show(True)
        wx.FutureCall(500,self.Download)

    def Download(self):
        pass

    def OnWizPageChanging(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()
        if self.Running == True:
            evt.Veto()

    def OnWizCancel(self, evt):
        page = evt.GetPage()
        #TODO: disable next/prev/cancel during download
        if self.Running == True:
            evt.Veto()

class UpgradeMcuPage(UpgradeDasPage):
    def __init__(self, parent, title, version ):
        UpgradeDasPage.__init__(self, parent, title, version)
        self.text1.SetLabel("Upgrading MCU image...")

    def Download(self):
        upgrade = DasUpgrade()
        self.Running = True

        self.status.SetValue("")

        # This doesn't work
        #nextButton = self.FindWindowById(wx.ID_FORWARD)
        #prevButton = self.FindWindowById(wx.ID_BACKWARD)
        #nextButton.Disable()
        #prevButton.Disable()

        filename = _IMAGES_DIRECTORY + self.version + " " + "f2812.hex"
        try:
            if upgrade.DasUpgrade_DownloadMcuImage(  self.version, filename, self.gauge, self.status )==False:
                _PrintStatus( self.status, "ERROR: Failed to download image!!" )
                self.SetNext( self.GetLast() )
            pass
        except:
            pass
        #nextButton.Enable()
        #prevButton.Enable()
        self.Running = False

class UpgradeDspPage(UpgradeDasPage):
    def __init__(self, parent, title, version ):
        UpgradeDasPage.__init__(self, parent, title, version)
        self.text1.SetLabel("Upgrading DSP image...")

    def Download(self):
        upgrade = DasUpgrade()
        self.Running = True
        self.status.SetValue("")
        filename = _IMAGES_DIRECTORY + self.version + " " + "6713.hex"
        if upgrade.DasUpgrade_DownloadDspImage( self.version, filename, self.gauge, self.status )==False:
            _PrintStatus( self.status, "Failed to download image." )
        self.Running = False

class UpgradeFpgaPage(UpgradeDasPage):
    def __init__(self, parent, title, version ):
        UpgradeDasPage.__init__(self, parent, title, version)
        self.text1.SetLabel("Upgrading FPGA image...")

    def Download(self):
        self.Running = True
        self.status.SetValue("")

        filename = _IMAGES_DIRECTORY + self.version + ".xsvf"
        upgrade = DasUpgrade()
        if upgrade.DasUpgrade_DownloadJtagImage( self.version, filename, self.gauge, self.status )==False:
            _PrintStatus( self.status, "Failed to download image." )

        self.Running = False

class UpgradeUsbPage(UpgradeDasPage):
    def __init__(self, parent, title, version ):
        UpgradeDasPage.__init__(self, parent, title, version)
        self.text1.SetLabel("Upgrading USB image...")

    def Download(self):
        self.Running = True
        self.status.SetValue("")

        filename = _IMAGES_DIRECTORY + self.version + ".iic"
        upgrade = DasUpgrade()
        if upgrade.DasUpgrade_DownloadUsbImage( self.version, filename, self.gauge, self.status ) == False:
            _PrintStatus( self.status, "Failed to download image." )
        self.Running = False

class UpgradePage(WizardTitledLogoPage):
    def __init__(self, parent, title ):
        WizardTitledLogoPage.__init__(self, parent, title)
        self.firsttime = True

        self.text1 = wx.StaticText( self, -1, """\nPlease select processor to upgrade:\n""", (1,1), (380,30))
        self.sizer.Add( self.text1 )
        self.password = ''

        # List of images to upgrade
        self.list = [ \
            ("MCU",  UpgradeMcuPage,   "  MCU Firmware Upgrade",  True) ,\
            ("DSP",  UpgradeDspPage,   "  DSP FirmwareUpgrade",  True) ,\
            ("FPGA", UpgradeFpgaPage,  "  FPGA Firmware Upgrade", False),\
            ("USB",  UpgradeUsbPage,   "  USB Firmware Upgrade", False),\
            ]
        self.cblist   = []
        for i in self.list:
            cb = wx.CheckBox(self, -1, i[0] )
            cb.SetValue( i[3] )
            self.sizer.Add( cb )
            self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, cb)
            self.cblist.append( cb )

        self.text2 = wx.StaticText( self, -1, """\nPlease select MCU/DSP version:\n""")
        self.sizer.Add( self.text2 )

        # Get versions for MCU/DSP images
        #
        # Expecting files to be name in the following way:
        # - for MCU Images: "X.Y_f2812.hex"
        # - for DSP Images: "X.Y_6713.hex"
        # where "X.Y" is a decimal number, and "_" is space.
        files = glob.glob(_IMAGES_DIRECTORY+"*.hex") #os.listdir( _IMAGES_DIRECTORY )
        versions = []
        for file in files:
            filepath,filename = os.path.split(file)
            args = filename.split(' ',2)
            if len(args) > 1:
                if not args[0] in versions:
                    versions.append( args[0] )
        if len(versions):
            versions.sort()
            versions.reverse()
            self.mcuDspVersionComboBox = wx.ComboBox( self, 500, "", (90, 50), \
                (250, -1), versions, wx.CB_DROPDOWN )
            self.sizer.Add( self.mcuDspVersionComboBox )
            self.mcuDspVersionComboBox.SetSelection( 0 )

        self.text3 = wx.StaticText( self, -1, """\nPlease select FPGA version:\n""")
        self.sizer.Add( self.text3 )

        # Get versions for FPGA images
        #
        files = glob.glob(_IMAGES_DIRECTORY+"*.xsvf") #os.listdir( _IMAGES_DIRECTORY )
        filelist = []
        for file in files:
            filepath,filename = os.path.split(file)
            filetime = os.path.getmtime(file)
            args = filename.split('.',2)
            if len(args) > 1:
                if not args[0] in filelist:
                    filelist.append( (filetime, args[0]) )
        if len(filelist):
            filelist.sort()
            filelist.reverse()
            versions = [f for t,f in filelist]
            self.fpgaVersionComboBox = wx.ComboBox( self, 500, "", (90, 50), \
                (250, -1), versions, wx.CB_DROPDOWN )
            self.sizer.Add( self.fpgaVersionComboBox )
            self.fpgaVersionComboBox.SetSelection( 0 )

        self.text4 = wx.StaticText( self, -1, """\nPlease select USB version:\n""")
        self.sizer.Add( self.text4 )

        # Get versions for USB images
        #
        files = glob.glob(_IMAGES_DIRECTORY+"*.iic") #os.listdir( _IMAGES_DIRECTORY )
        filelist = []
        for file in files:
            filepath,filename = os.path.split(file)
            filetime = os.path.getmtime(file)
            args = filename.split('.',2)
            if len(args) > 1:
                if not args[0] in filelist:
                    filelist.append( (filetime, args[0]) )
        if len(filelist):
            filelist.sort()
            filelist.reverse()
            versions = [f for t,f in filelist]
            self.usbVersionComboBox = wx.ComboBox( self, 500, "", (90, 50), \
                (250, -1), versions, wx.CB_DROPDOWN )
            self.sizer.Add( self.usbVersionComboBox )
            self.usbVersionComboBox.SetSelection( 0 )

        # Create pages
        self.pagelist = []
        for i in self.list:
            if i[0]=="MCU" or i[0]=="DSP":
                version = self.mcuDspVersionComboBox.GetValue()
            elif i[0]=="FPGA":
                version = self.fpgaVersionComboBox.GetValue()
            elif i[0]=="USB":
                version = self.usbVersionComboBox.GetValue()
            page = i[1]( parent, i[2], version )
            self.pagelist.append( page )

        # Bind events
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnWizPageChanged)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnWizPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnWizCancel)

    def EnablePage(self, Flag):
        if Flag == True:
            self.mcuDspVersionComboBox.Enable()
            for i in self.cblist:
                i.Enable()
            self.text1.Enable()
            self.text2.Enable()
            self.fpgaVersionComboBox.Enable()
            self.usbVersionComboBox.Enable()
        else:
            self.mcuDspVersionComboBox.Disable()
            for i in self.cblist:
                i.Disable()
            self.text1.Disable()
            self.text2.Disable()
            self.fpgaVersionComboBox.Disable()
            self.usbVersionComboBox.Disable()

    def OnWizPageChanged(self, evt):

        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()

        if _PROMPT_PASSWORD == True:
            dlg = wx.TextEntryDialog(self, 'Password: ','Authorization required', '', wx.OK | wx.CANCEL | wx.TE_PASSWORD)
            if ( self.password != _UpgradePassword ):
                status = dlg.ShowModal()
                self.password = dlg.GetValue()
            else:
                status = wx.ID_OK
            if ( self.password != _UpgradePassword or status != wx.ID_OK ) :
                dlg.Destroy()
                dlg = wx.MessageDialog(self,'Permission denied.','Firmware Upgrade', wx.OK )
                dlg.ShowModal()
                dlg.Destroy()
                self.EnablePage(False)
                return
            self.EnablePage(True)
            dlg.Destroy()

        if self.firsttime == True:
            self.lastPage = self.next
            self.firstPage = self.prev
            self.firsttime = False
            self.SetupPages()

    def OnWizPageChanging(self, evt):
        version = self.mcuDspVersionComboBox.GetValue()
        self.pagelist[_MCU_PAGE].version = version
        self.pagelist[_DSP_PAGE].version = version
        version = self.fpgaVersionComboBox.GetValue()
        self.pagelist[_FPGA_PAGE].version = version
        version = self.usbVersionComboBox.GetValue()
        self.pagelist[_USB_PAGE].version = version

        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()

    def OnWizCancel(self, evt):
        page = evt.GetPage()
        # Show how to prevent cancelling of the wizard.  The
        # other events can be Veto'd too.
        #if page is self.page1:
        #    wx.MessageBox("Cancelling on the first page has been prevented.", "Sorry")
        #    evt.Veto()

    def OnWizFinished(self, evt):
        pass

    def SetupPages( self ):
        prevPage = self
        page     = self
        for i in range( len(self.list) ):
            if self.cblist[i].IsChecked():
                page = self.pagelist[i]
                page.SetPrev( prevPage )
                page.SetLast( self.lastPage )
                prevPage.SetNext( page )
                prevPage = page
            else:
                prevPage.SetNext( page.next )
                prevPage = page
        page.SetNext( self.lastPage )
        self.lastPage.SetPrev ( page )

    def EvtCheckBox(self, event):
        self.SetupPages()
