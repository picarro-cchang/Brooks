# File Name: DasMaintenanceGui.py
# Purpose: This module handles the Gui for the DAS Maintenance GUI
#
# File History:
# 06-05-02 ytsai   Created file
# 06-05-15 ytsai   Added register save

import os, sys
import wx
import wx.wizard as wiz
import time
import getopt

from wizardhelper       import WizardTitledLogoPage
from DasUpgradeGui      import UpgradePage
from DasDiagSaveGui     import SaveDasDiagPage
from DasRegisterSaveGui import SaveDasRegPage

sys.path.append("../../Common")
import CmdFIFO as CmdFIFO

sys.path.append("../../Supervisor")
from Supervisor import RPC_SERVER_PORT_MASTER

class MainPage(WizardTitledLogoPage):
    def __init__(self, parent, title, list ):
        WizardTitledLogoPage.__init__(self, parent, title)

        text1 = wx.StaticText( self, -1, """To add a task to perform, click on the checkbox below.\n""")
        self.sizer.Add( text1 )

        self.listbox = wx.CheckListBox( self, -1, (1, 1), (380,188) )
        self.sizer.Add( self.listbox, 0, wx.EXPAND|wx.ALL, 1)
        for i in list:
            (name,page,description) = i
            self.listbox.Append( name )

        self.Bind(wx.EVT_CHECKLISTBOX, self.EvtCheckListBox, self.listbox )

    def CreatePages( self, wizard, lastPage, list ):
        self.lastPage = lastPage
        self.wizard   = wizard
        self.pagelist = []
        for tuple in list:
            (Name,PageClass,Description) = tuple
            page = PageClass( wizard, Name )
            self.pagelist.append( page )

    def SetupPages( self ):
        prevPage = self
        page     = self
        for i in range( self.listbox.GetCount() ):
            if self.listbox.IsChecked(i):
                page = self.pagelist[i]
                page.SetPrev( prevPage )
                prevPage.SetNext( page )
                prevPage = page
            else:
                prevPage.SetNext( page.next )
                prevPage = page
        page.SetNext( self.lastPage )
        self.lastPage.SetPrev ( page )

    def EvtCheckListBox(self, event):
        self.SetupPages()

class LastPage(WizardTitledLogoPage):
    def __init__(self, parent, title ):
        WizardTitledLogoPage.__init__(self, parent, title)

        text1 = wx.StaticText( self, -1, """Tasks completed.\nPlease power cycle DAS.""")
        self.sizer.Add( text1 )

class DasApp(wx.PySimpleApp):
    def OnInit(self):
        # Shut down other python apps so they won't interfere with downloads
        try:
            rpcServer = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_SERVER_PORT_MASTER, ClientName = "Maintenance")
            #dlg = wx.SingleChoiceDialog(frame, "Terminate other Silverstone App(s)?" ,'Warning',['Yes','No'], wx.CHOICEDLG_STYLE)
            #if dlg.ShowModal() == wx.ID_OK:
            # if dlg.GetStringSelection() == 'Yes':
            rpcServer.TerminateApplications()
            time.sleep( 1 )
        except:
            pass

        return True

    def Run(self, UpgradeFlag=True):
        frame  = wx.Frame(None)

        # create wizards
        self.wizard = wiz.Wizard( frame, -1, "CRDS Maintenance Tool"   )

        self.lastPage = LastPage( self.wizard, "  CRDS Maintenance" )

        if UpgradeFlag == True:
            self.mainPage = UpgradePage( self.wizard, 'Upgrade DAS Firmware(s)' )
            self.mainPage.SetNext ( self.lastPage )
            self.lastPage.SetPrev ( self.mainPage )
        else:
            taskList = []
            taskList.append( ('Save DAS Diagnostics',    SaveDasDiagPage, 'Collects diagnostics information from DAS' ) )
            taskList.append( ('Save DAS Registers',      SaveDasRegPage,  'Read and save registers read from DAS' ) )
            self.mainPage = MainPage( self.wizard, "  CRDS Maintenance", taskList )
            self.mainPage.SetNext ( self.lastPage )
            self.lastPage.SetPrev ( self.mainPage )
            self.mainPage.CreatePages( self.wizard, self.lastPage, taskList )

        self.wizard.FitToPage( self.mainPage )
        self.wizard.RunWizard( self.mainPage )

# Usage
def Usage():
    """
    Purpose:    Display Usage
    Arguments:  None
    Returns:    None
    Exceptions: None
    """
    print "-h\tDisplay help.\n-u\tUpgrade MCU/DSP firmware.\n"

# Main
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu", ["help", "upgrade"])
    except getopt.GetoptError:
        # print help information and exit:
        Usage()
        sys.exit(2)

    upgradeFlag = False

    for o, a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        if o in ("-u", "--upgrade"):
            upgradeFlag = True

    app = DasApp()
    app.Run( upgradeFlag )

if __name__ == "__main__" :
    main()
