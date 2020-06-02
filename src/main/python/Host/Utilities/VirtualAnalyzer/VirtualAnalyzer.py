import wx
import re
import os
import sys
import gettext

if os.name == 'posix' and sys.version_info[0] < 3:
    import subprocess32 as subprocess
else:
    import subprocess

#SUPERVISORLAUNCHER_PATH = r'C:\Picarro\G2000\AppConfig\Config\Utilities\SupervisorLauncher.ini'

# Linux RSF
DEV_DIR = r'/home/rsf/git/host/src/main/python/'
SUPERVISORLAUNCHERINI_PATH = DEV_DIR + r'/AppConfig/Config/Utilities/SupervisorLauncher.ini'
SUPERVISOR_PATH = r'/Host/Supervisor/'
SUPERVISOREXE_PATH = 'Supervisor.py'


class SupervisorModeDlg(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: SupervisorModeDlg.__init__
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_3 = wx.StaticText(self, wx.ID_ANY, _("Select supervisor mode for the analyzer:"))
        self.choice_mode = wx.Choice(self, wx.ID_ANY, choices=[])
        self.btnNext = wx.Button(self, wx.ID_ANY, _("Next"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnNextDlgClicked, self.btnNext)
        # end wxGlade

        if not os.path.exists(SUPERVISORLAUNCHERINI_PATH):
            raise Exception("Config file for supervisorLauncher not found: '%s'" % SUPERVISORLAUNCHERINI_PATH)
        with open(SUPERVISORLAUNCHERINI_PATH) as f:
            self.config = []
            self.selection = None
            content = f.read()
            for line in content.split("\n"):
                if re.match(r"\[.*\]", line):
                    section = re.sub(r"\[(.*)\]", r'\1', line)
                elif re.match(r"SupervisorIniFile\s*=\s*.*", line):
                    iniFile = re.sub(r"SupervisorIniFile\s*=\s*(.*\.ini)\s*", r'\1', line)
                    self.choice_mode.Append(section)
                    self.config.append(iniFile)
            if self.choice_mode.GetCount() > 0:
                self.choice_mode.SetSelection(0)

    def __set_properties(self):
        # begin wxGlade: SupervisorModeDlg.__set_properties
        self.SetTitle(_("Select Supervisor Mode"))
        self.label_3.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: SupervisorModeDlg.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_3.Add(self.label_3, 0, wx.ALL, 10)
        sizer_3.Add(self.choice_mode, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer_1.Add(sizer_3, 1, 0, 0)
        sizer_1.Add(self.btnNext, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        self.Centre()
        # end wxGlade

#    def OnNextDlgClicked(self, event):
#        index = self.choice_mode.GetCurrentSelection()
#        ini = os.path.join(r"..\AppConfig\Config\Supervisor", self.config[index])
#        os.chdir("HostExe")
#        args = [r'Supervisor.exe', '--vi', r'..\rdReprocessor.ini', '-c', ini]
#        subprocess.Popen(args)
#        self.Destroy()

# Linux version, hardcoded for git
#

    def OnNextDlgClicked(self, event):
        index = self.choice_mode.GetCurrentSelection()
        ini = os.path.join(DEV_DIR + r"/AppConfig/Config/Supervisor", self.config[index])
        os.chdir(DEV_DIR + SUPERVISOR_PATH)
        rdReprocessorIni = '/home/rsf/git/host/src/main/python/Host/Utilities/VirtualAnalyzer/rdReprocessor.ini'
        args = ['python', 'Supervisor.py', '--vi', rdReprocessorIni, '-c', ini]
        termList = ['xterm', '-hold', '-T', 'Supervisor', '-e']
        print(termList + args)
        #subprocess.Popen(termList + args)
        #self.Destroy()


# end of class SupervisorModeDlg
if __name__ == "__main__":
    gettext.install("app")  # replace with the appropriate catalog name

    # app = wx.PySimpleApp(0)
    app = wx.App(False)
    # wx.InitAllImageHandlers()
    SupervisorMode = SupervisorModeDlg(None, wx.ID_ANY, "")
    app.SetTopWindow(SupervisorMode)
    SupervisorMode.Show()
    app.MainLoop()
