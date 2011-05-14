"""
File Name: IPVLicense.py
Purpose:
    IPV License Software

File History:
    11-03-03 Alex  Created

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

import os
import sys
import wx
import getopt
import time
from Host.Common.CustomConfigObj import CustomConfigObj
from datetime import datetime, timedelta

MESSAGE_LIST = \
[
r"""What is IPV?

Picarro's Instrument Performance Verification (IPV) is a software service designed to allow Picarro support engineers to monitor key sensors embedded within Picarro instruments and automatically detect instrument anomalies. IPV allows Picarro's support team to move quickly to correct problems and, in some cases, react to potential instrument problems before they happen.

How does it work?

The IPV service continuously monitors instrument "health" by collecting readings from sophisticated internal sensors and measuring key performance metrics for critical analyzer components. This information is automatically transmitted to Picarro's support team via the Internet.

For more information, please visit:
http://www.picarro.com/gas_analyzers/peripherals/ipv""",

r"""Your %d-Day IPV Trial has ended!
                                                           
With IPV, Picarro can monitor your instruments around the world and around the clock, so you don't have to. IPV allows Picarro's support team to move quickly to correct problems and, in some cases, react to potential instrument problems before they happen.

IPV has been disabled on your instrument. If you would like to continue to use IPV, please contact your Picarro sales representative, or send an email to support@picarro.com
""",

r"""Your %d-Day IPV Subscription has ended!
                                                               
With IPV, Picarro can monitor your instruments around the world and around the clock, so you don't have to. IPV allows Picarro's support team to move quickly to correct problems and, in some cases, react to potential instrument problems before they happen.

IPV has been disabled on your instrument. If you would like to continue to use IPV, please contact your Picarro sales representative, or send an email to support@picarro.com
"""
]

TITLE_LIST = \
[ "%d-Day Trial",
"%d-Day Trial",
"%d-Day Subscription"
]  

YES_BUTTON_LIST = ["Activate IPV Trial", "OK", "OK"]

class IPVLicenseFrame(wx.Frame):
    def __init__(self, selector, trialDays, *args, **kwds):
        kwds["style"] = (wx.CAPTION|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.TAB_TRAVERSAL|wx.STAY_ON_TOP) &~ (wx.CLOSE_BOX)
        #kwds["style"] = wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.RESIZE_BOX|wx.MAXIMIZE_BOX)
        wx.Frame.__init__(self, *args, **kwds)
        self.panel1 = wx.Panel(self, -1)
        self.panel2 = wx.Panel(self, -1)
        self.panel1.SetBackgroundColour("#E0FFFF")
        self.panel2.SetBackgroundColour("#BDEDFF")
        self.SetTitle("Instrument Performance Verification - " + TITLE_LIST[selector] % trialDays)
        self.labelTitle = wx.StaticText(self.panel1, -1, "Picarro Instrument Performance Verification (IPV)")
        self.labelTitle.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.labelTitle2 = wx.StaticText(self.panel1, -1, TITLE_LIST[selector] % trialDays)
        self.labelTitle2.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.staticLine = wx.StaticLine(self.panel2, -1)
        self.labelFooter = wx.StaticText(self.panel2, -1, "Copyright Picarro, Inc. 1999-2011", style=wx.ALIGN_CENTER)
        self.textCtrlMessage = wx.TextCtrl(self.panel2, -1, "", style = wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH|wx.TE_LEFT)
        self.textCtrlMessage.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.textCtrlMessage.SetMinSize((500,300))
        if selector == 0:
            self.textCtrlMessage.WriteText(MESSAGE_LIST[selector])
        else:
            self.textCtrlMessage.WriteText(MESSAGE_LIST[selector] % trialDays)
        self.textCtrlMessage.SetInsertionPoint(0)
        if selector == 0:
            self.textCtrlMessage.SetStyle(0, 12, wx.TextAttr(wx.NullColour, wx.NullColour, wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")))
            self.textCtrlMessage.SetStyle(388, 405, wx.TextAttr(wx.NullColour, wx.NullColour, wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")))
        else:
            self.textCtrlMessage.SetStyle(0, 45, wx.TextAttr(wx.NullColour, wx.NullColour, wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, "")))

        # Buttons
        self.buttonAnsYes = wx.Button(self.panel2, -1, YES_BUTTON_LIST[selector], style=wx.BU_EXACTFIT)
        self.buttonAnsYes.SetFocus()
        self.buttonAnsNo = wx.Button(self.panel2, -1, "No Thanks", style=wx.BU_EXACTFIT)             
        self.buttonRemind = wx.Button(self.panel2, -1, "Remind me later", style=wx.BU_EXACTFIT) 
        self.buttonAnsYes.SetMinSize((170, 25))
        self.buttonAnsYes.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonAnsYes.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonAnsNo.SetMinSize((170, 25))
        self.buttonAnsNo.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonAnsNo.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.buttonRemind.SetMinSize((170, 25))
        self.buttonRemind.SetBackgroundColour(wx.Colour(237, 228, 199))
        self.buttonRemind.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        
        if selector == 1:
            self.buttonAnsNo.Destroy()
        
        self.__do_layout()

    def __do_layout(self):
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.VERTICAL)

        sizer_1.Add(self.labelTitle, 0, wx.TOP|wx.ALIGN_CENTER, 10)
        sizer_1.Add(self.labelTitle2, 0, wx.BOTTOM|wx.ALIGN_CENTER, 10)
        self.panel1.SetSizer(sizer_1)
        
        sizer_2.Add(self.staticLine, 0, wx.EXPAND|wx.BOTTOM, 5)
        sizer_2.Add(self.textCtrlMessage, 0, wx.LEFT|wx.RIGHT, 10)
        
        sizer_3.Add(self.buttonAnsYes, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        if selector == 0:
            sizer_3.Add(self.buttonAnsNo, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        else:
            sizer_3.Add(self.buttonRemind, 0, wx.ALL|wx.ALIGN_CENTER, 10)
        
        sizer_4.Add(sizer_2, 0, wx.BOTTOM, 20)
        sizer_4.Add(sizer_3, 0, wx.LEFT, 70)
        sizer_4.Add((-1,5))
        if selector == 0:
            sizer_4.Add(self.buttonRemind, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        sizer_4.Add(self.labelFooter, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel2.SetSizer(sizer_4)
        
        sizer_5.Add(self.panel1, 0, wx.EXPAND, 0)
        sizer_5.Add(self.panel2, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_5)
        sizer_5.Fit(self)
        self.Layout()

class IPVLicense(IPVLicenseFrame):
    def __init__(self, configFile, selector, trialDays, remindDays, *args, **kwds):
        self.cp = CustomConfigObj(configFile)
        self.selector = selector
        self.trialDays = trialDays 
        self.remindDays = remindDays
        IPVLicenseFrame.__init__(self, selector, trialDays, *args, **kwds)
        self.bindEvents()
        if selector != 0:        
            self.cp.set("Main", "enabled", "False")
            self.cp.write()
            self.killIPV()
        self.renewMsgSelector = self.cp.getint("License", "renewMsgSelector", 1)
        if self.renewMsgSelector not in [1,2]:
            self.renewMsgSelector = 1
        f1=os.popen("echo %userdomain%","r")
        f2=os.popen("echo %username%","r")
        d=f1.read().strip()
        u=f2.read().strip()
        self.user = "%s\%s" % (d,u)
        self.password = "picarro"
        
    def bindEvents(self):
        self.Bind(wx.EVT_TEXT_URL, self.onOverUrl, self.textCtrlMessage)
        self.Bind(wx.EVT_BUTTON, self.onRemindButton, self.buttonRemind) 
        if self.selector == 0:
            self.Bind(wx.EVT_BUTTON, self.onYesButton, self.buttonAnsYes)
            self.Bind(wx.EVT_BUTTON, self.onNoButton, self.buttonAnsNo)
        else:
            self.Bind(wx.EVT_BUTTON, self.onOKButton, self.buttonAnsYes)   

    def onOverUrl(self, event):
        if event.MouseEvent.LeftDown():
            urlString = self.textCtrlMessage.GetRange(event.GetURLStart(), event.GetURLEnd())
            print urlString
            wx.LaunchDefaultBrowser(urlString)
        else:
            event.Skip()
            
    def onYesButton(self, event):
        self.cp.set("Main", "enabled", "True")
        self.cp.write()
        self.killIPV()
        nextRunTime = datetime.now()+ timedelta(days=self.trialDays)
        startTime = datetime.strftime(nextRunTime, "%H:%M:%S")
        startDate = datetime.strftime(nextRunTime, "%m/%d/%Y")
        os.system(r'schtasks.exe /delete /tn IPVLicense /f')
        os.system(r'schtasks.exe /create /tn IPVLicense /tr "C:\Picarro\G2000\HostExe\IPVLicense.exe -s %d -r %f -t %f" /sc ONCE /st %s /sd %s /ru %s /rp %s' % (self.renewMsgSelector, self.remindDays, self.trialDays, startTime, startDate, self.user, self.password))
        self.Destroy()

    def onOKButton(self, event):
        self.Destroy()
        
    def onNoButton(self, event):
        self.cp.set("Main", "enabled", "False")
        self.cp.write()
        self.killIPV()
        self.Destroy()

    def onRemindButton(self, event):
        nextRunTime = datetime.now()+ timedelta(days=self.remindDays)
        startTime = datetime.strftime(nextRunTime, "%H:%M:%S")
        startDate = datetime.strftime(nextRunTime, "%m/%d/%Y")
        os.system(r'schtasks.exe /delete /tn IPVLicense /f')
        os.system(r'schtasks.exe /create /tn IPVLicense /tr "C:\Picarro\G2000\HostExe\IPVLicense.exe -s %d -r %f -t %f" /sc ONCE /st %s /sd %s /ru %s /rp %s' % (self.selector, self.remindDays, self.trialDays, startTime, startDate, self.user, self.password))
        self.Destroy()
 
    def killIPV(self):
        os.system(r'taskkill.exe /IM IPV.exe /F')
        
def handleCommandSwitches():
    shortOpts = "c:s:t:r:"
    longOpts = []
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    configFile = r"C:\Picarro\G2000\InstrConfig\InstrIPV.ini"
    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
        
    selector = 0
    if "-s" in options:
        selector = int(options["-s"])  
        
    trialDays = 90.0
    if "-t" in options:
        trialDays = float(options["-t"])  
        
    remindDays = 3.0
    if "-r" in options:
        remindDays = float(options["-r"]) 
        
    return configFile, selector, trialDays, remindDays
    
if __name__ == "__main__" :
    configFile, selector, trialDays, remindDays = handleCommandSwitches()
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame = IPVLicense(configFile, selector, trialDays, remindDays, None, -1, "")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()