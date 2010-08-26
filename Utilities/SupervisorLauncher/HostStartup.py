import sys
import os
import wx
import win32api
import win32process
import win32con
import time
import getopt
from configobj import ConfigObj

translationTable = {
"supervisor.exe": "Supervisor",
"eventmanager.exe": "Event Manager",
"driver.exe": "Driver",
"archiver.exe": "Data Archiver",
"rdfrequencyconverter.exe": "Ring-down Frequency Converter",
"spectrumcollector.exe": "Spectrum Collector",
"fitter.exe": "Fitter",
"meassystem.exe": "Measurement System",
"datamanager.exe": "Data Manager",
"samplemanager.exe": "Sample Manager",
"instmgr.exe": "Instrument Manager",
"alarmsystem.exe": "Alarm System",
"valvesequencer.exe": "Valve Sequencer",
"quickgui.exe": "CRDS Data Viewer",
"electricalinterface.exe": "Electrical Interface",
"controller.exe": "Controller"
}

appTimeout = 30 # sec

#Set up a useful AppPath reference...
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

def getWinProcessListStr():
    pList = win32process.EnumProcesses()
    moduleList = []
    for p in pList:
        try:
            h = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,0,p)
            moduleList.append(win32process.GetModuleFileNameEx(h,None).lower())
        except Exception,e:
            pass
            #print "Cannot fetch information for %s: %s" % (p,e)
    processListStr = "\n".join(moduleList)
    return processListStr
    
class HostStartupFrame(wx.Frame):
    def __init__(self, taskList, *args, **kwds):
        self.taskList = taskList
        kwds["style"] = wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL|wx.STAY_ON_TOP
        kwds["pos"] = (0,20)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel2 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel3 = wx.Panel(self, -1, style=wx.TAB_TRAVERSAL|wx.ALWAYS_SHOW_SB)
        self.panel1.SetBackgroundColour("white")
        self.panel2.SetBackgroundColour("#E0FFFF")
        self.panel3.SetBackgroundColour("#BDEDFF")
        self.SetTitle("Picarro Software Loading Status")
        self.CenterOnScreen(wx.HORIZONTAL)

        # labels
        self.labelTitle1 = wx.StaticText(self.panel1, -1, "CRDS Software Loading Status", style=wx.ALIGN_CENTRE)
        self.labelTitle1.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelFooter = wx.StaticText(self.panel3, -1, "Copyright Picarro, Inc. 1999-2010", style=wx.ALIGN_CENTER)
        
        # Current status display 
        self.curTextList = []        
        self.curCheckboxList = []
        for idx in range(len(self.taskList)):
            try:
                displayName = translationTable[self.taskList[idx]]
            except:
                displayName = self.taskList[idx].split(".")[0]
            staticText = wx.StaticText(self.panel2, -1, displayName, style=wx.TE_CENTRE)
            staticText.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
            self.curTextList.append(staticText)
            self.curCheckboxList.append((20,20))
        
        # Divider line
        self.staticLine = wx.StaticLine(self.panel1, -1)      
        
        # Image
        logoBmp = wx.Bitmap(os.path.dirname(AppPath)+'/logo.png', wx.BITMAP_TYPE_PNG)
        self.logoImage = wx.StaticBitmap(self.panel1, -1, logoBmp)
        
        self.do_layout()
        
    def do_layout(self, checkList = [], idleList = []):
        logoSizer = wx.BoxSizer(wx.VERTICAL)
        logoSizer.Add(self.logoImage, 0, wx.TOP, 15)
        sizer_all = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.FlexGridSizer(-1, 3)

        sizer_1.Add(logoSizer, 0, wx.ALIGN_CENTER|wx.BOTTOM, 5)
        sizer_1.Add(self.labelTitle1, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER, 20)
        sizer_1.Add(self.staticLine, 0, wx.EXPAND, 0)
        self.panel1.SetSizer(sizer_1)
        
        for idx in range(len(self.taskList)):
            grid_sizer_1.Add((50,-1))
            if idx in checkList:
                checkBmp = wx.Bitmap(os.path.dirname(AppPath)+'/Check.png', wx.BITMAP_TYPE_PNG)
                checkImage = wx.StaticBitmap(self.panel2, -1, checkBmp)
                grid_sizer_1.Add(checkImage, 0, wx.ALL, 10)
            elif idx in idleList:
                checkBmp = wx.Bitmap(os.path.dirname(AppPath)+'/alarm.png', wx.BITMAP_TYPE_PNG)
                checkImage = wx.StaticBitmap(self.panel2, -1, checkBmp)
                grid_sizer_1.Add(checkImage, 0, wx.ALL, 10)
            else:
                grid_sizer_1.Add(self.curCheckboxList[idx], 0, wx.ALL, 10)
                
            grid_sizer_1.Add(self.curTextList[idx], 0, wx.ALL, 10)
        sizer_2.Add(grid_sizer_1, 0, wx.EXPAND, wx.RIGHT|wx.LEFT, 20)
        self.panel2.SetSizer(sizer_2)
        
        sizer_3.Add(self.labelFooter, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
        self.panel3.SetSizer(sizer_3)
        
        sizer_all.Add(self.panel1, 0, wx.EXPAND)
        sizer_all.Add(self.panel2, 0, wx.EXPAND)
        sizer_all.Add(self.panel3, 0, wx.EXPAND)
        self.SetSizer(sizer_all)
        sizer_all.Fit(self)
        #self.SetSize((600, -1))  
        self.Layout()

class HostStartup(HostStartupFrame):
    def __init__(self, configFile, *args, **kwds):
        self.co = ConfigObj(configFile)
        taskList = []
        fitterFound = False
        for appName in self.co["Applications"]:
            if appName == "RDFreqConverter":
                taskList.append("rdfrequencyconverter.exe")
            elif appName.startswith("Fitter"):
                if not fitterFound:
                    taskList.append("fitter.exe")
                    fitterFound = True
            else:
                taskName = "%s.exe" % appName
                taskList.append(taskName.lower())
            if appName == "QuickGui":
                break
        HostStartupFrame.__init__(self, taskList, *args, **kwds)
        self.taskIdx = 0
        self.timer = wx.Timer(self)
        self.timer.Start(100)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)  
        self.startedList = []
        self.idleList = []
        self.startTime = time.time()
        
    def onTimer(self, event):
        if self.taskIdx == len(self.taskList):
            self.Destroy()
            return
        winProcessListStr = getWinProcessListStr()
        if self.taskList[self.taskIdx] in winProcessListStr:
            self.curTextList[self.taskIdx].SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
            self.startedList.append(self.taskIdx)
            self.do_layout(self.startedList, self.idleList)
            self.startTime = time.time()
            self.taskIdx += 1
        else:
            if (time.time() - self.startTime) < appTimeout:
                return
            else:
                self.idleList.append(self.taskIdx)
                self.do_layout(self.startedList, self.idleList)
                self.startTime = time.time()
                self.taskIdx += 1

HELP_STRING = \
"""

HostStartup.py [-h] [-c <FILENAME>]

Where the options can be a combination of the following:
-h, --help : Print this help.
-c         : Specify a config file.

"""

def PrintUsage():
    print HELP_STRING
    
def HandleCommandSwitches():
    import getopt

    try:
        switches, args = getopt.getopt(sys.argv[1:], "hc:", ["help"])
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    configFile = ""
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile
    
if __name__ == "__main__":
    configFile = HandleCommandSwitches()
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = HostStartup(configFile, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()