# File Name: DasDiagSaveGui.py
# Purpose: This module is responsible for the GUI for the upgrader
#
# File History:
# 06-05-11 ytsai   Created file

import sys
import os
import wx
import wx.wizard as wiz
from   wizardhelper  import WizardTitledLogoPage
import time

sys.path.append("../..")
sys.path.append("../../Common")
sys.path.append("../../Driver")
import DasDiag
import ss_autogen as Global
import DasInterface

class SaveDasDiagPage (WizardTitledLogoPage):
    def __init__(self, parent, title ):
        WizardTitledLogoPage.__init__(self, parent, title)

        text1 = wx.StaticText( self, -1, """Saving Das Diagnostics...\n""")
        self.sizer.Add( text1, 0, wx.EXPAND | wx.ALL, 5  )

        self.gauge = wx.Gauge(self, -1, 50, (510, 250), (450, 30))
        self.gauge.SetBezelFace(3)
        self.gauge.SetShadowWidth(3)
        self.sizer.Add( self.gauge, 0, wx.ALIGN_BOTTOM | wx.EXPAND | wx.ALL, 5 )

        self.status = wx.StaticText( self, -1, """ """)
        self.sizer.Add( self.status, 0, wx.EXPAND | wx.ALL, 5 )

        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGED, self.OnWizPageChanged)
        self.Bind(wiz.EVT_WIZARD_PAGE_CHANGING, self.OnWizPageChanging)
        self.Bind(wiz.EVT_WIZARD_CANCEL, self.OnWizCancel)


        self.Running = False

    def OnWizPageChanged(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
            return

        if self.Running == True:
            return
        page = evt.GetPage()
        self.Show(True)
        diag = DasDiag.Diag()
        self.Running = True

        try:
            version = DasInterface.rdPDasReg(Global.VERSION_REGISTER,Global.VERSION_mcu)
        except:
            self.status.SetLabel("Failed. Unable to read mcu version" )
            self.Running = False
            return

        if version < 3.0:
            self.status.SetLabel("Failed. Invalid MCU version %0.2f" % version )
            self.Running = False
            return

        filename = time.strftime("Logs/Diag%Y%m%d_%H%M%S.log",time.localtime())
        self.gauge.SetRange( 1 )
        self.gauge.SetValue( 0 )
        wx.Yield()
        status = diag.DIAG_SaveTables( filename )
        if status == True:
            self.status.SetLabel("Done.")
        else:
            self.status.SetLabel("Failed.")
        self.gauge.SetValue( 1 )
        self.Running = False

    def OnWizPageChanging(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()

    def OnWizCancel(self, evt):
        page = evt.GetPage()

if __name__ == "__main__":
    print "This file is for import only.  It does nothing when executed on its own."
    pass
