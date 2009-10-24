# File Name: DasRegSaveGui.py
# Purpose: This module is responsible for saving DAS registers.
# File History:
# 06-05-15 ytsai   Created file

import sys
import os
import wx
import wx.wizard as wiz
from   wizardhelper  import WizardTitledLogoPage
import time
import ctypes

sys.path.append("../..")
sys.path.append("../../Common")
sys.path.append("../../Driver")
import ss_autogen as Global
import DasInterface

class SaveDasRegPage (WizardTitledLogoPage):
    def __init__(self, parent, title ):
        WizardTitledLogoPage.__init__(self, parent, title)

        text1 = wx.StaticText( self, -1, """Saving Das Registers\n""")
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
        self.Running = True

        filename = time.strftime("Logs/Reg%Y%m%d_%H%M%S.log",time.localtime())
        status = self.SaveRegisters(filename, self.gauge)
        if status == True:
            self.status.SetLabel("Done.")
        else:
            self.status.SetLabel("Failed.")
        self.Running = False

    def OnWizPageChanging(self, evt):
        if evt.GetDirection():
            dir = "forward"
        else:
            dir = "backward"
        page = evt.GetPage()

    def OnWizCancel(self, evt):
        page = evt.GetPage()

    def Print( self, fp, message ):
        print message
        fp.write(message + "\n")

    def SaveRegisters( self, filename, gauge=None ):
        fp = file( filename, 'w')

        try:
            version = DasInterface.rdPDasReg(Global.VERSION_REGISTER,Global.VERSION_mcu)
        except:
            self.status.SetLabel("Failed. Unable to read mcu version" )
            return False

        if version < 2.5:
            self.status.SetLabel("Failed. Invalid MCU version %0.2f" % version )
            return False

        fp.write("Version, %00.2f\n" % version )

        if gauge!=None:
            gauge.SetRange( Global.INTERFACE_NUMBER_OF_REGISTERS )

        for register in range( Global.INTERFACE_NUMBER_OF_REGISTERS ) :
            if gauge!=None:
                gauge.SetValue( register )
                wx.Yield()

            registerInfo  = Global.register_info[register]

            if registerInfo.name.startswith("FPGA_"):
                self.Print (fp, "R%03d: Skipped %s" % (register,registerInfo.name))
                continue

            rtype = registerInfo.rtype
            if type(rtype) == type(ctypes.Structure):
                self.Print (fp, "R%03d: Ignored %s" % (register,registerInfo.name))
                continue

            if registerInfo.name.startswith("IOMGR_FLOAT") or\
                registerInfo.name.startswith("IOMGR_ADC")  or\
                registerInfo.name.startswith("IOMGR_DAC")  or\
                registerInfo.name.startswith("IOMGR_HEATER")    :
                self.Print (fp,"R%03d: Ignored %s" % (register,registerInfo.name))
                continue

            # Hard coded workaround - if register number is 592, DAS will reset.
            if version == 2.5 and register >= 592:
                return True

            if registerInfo.readable==True and registerInfo.haspayload==False:
                try:
                    value = DasInterface.rdDasReg( register )
                    self.Print (fp, "R%03d, %r, %s" % (register,value, registerInfo.name))
                except:
                    self.Print (fp, "R%03d, Failed, %s" % (register,registerInfo.name))
                    pass
            else:
                pass
            wx.Yield()
        return True


if __name__ == "__main__":
    print "This file is for import only.  It does nothing when executed on its own."
    pass
