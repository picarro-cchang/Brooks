#!/usr/bin/env python
#
# File Name: TestClient.py
#
# File History:
# 05-09-12 russ  Created first release.
# 06-02-16 russ  Sorted and left justified rpc buttons; (several un-doc'd before this)

"""This executable script provides a generic GUI for accessing all applications
that use CmdFIFO server.

All available RPC calls are available (with help in the form of docstrings for
each).

In addition, all core CmdFIFO calls are available.

For instructions on how to use, use the -h command line switch to get:

"""

HELP_STRING = \
""" TestClient.py [options]

Where the options can be a combination of the following:
-h, --help           print this help.
-a, --serveraddr     Specify the server address to link to [127.0.0.1]
-p, --serverport     Specify the server port to link to [8001]
-c, --callbackaddr   Specify the port that the client will listen on for
                     callbacks [8002]
-s, --simple         Start in simple mode (does not query the server for the
                     supported command set).  Only core CmdFIFO functions will
                     be available.
"""
__doc__ += HELP_STRING

from sys import path as sys_path
if "../Common" not in sys_path: sys_path.append("../Common")
import wx
import Host.Common.CmdFIFO as CmdFIFO
#import Host.Common.BetterTraceback as BetterTraceback

CmdTypeChoicesDict = {
    "CMD_TYPE_Default"   : CmdFIFO.CMD_TYPE_Default,
    "CMD_TYPE_Blocking"  : CmdFIFO.CMD_TYPE_Blocking,
    "CMD_TYPE_VerifyOnly": CmdFIFO.CMD_TYPE_VerifyOnly,
    "CMD_TYPE_Callback"  : CmdFIFO.CMD_TYPE_Callback,
    }


class MyMenuBar(wx.MenuBar):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyMenuBar.__init__
        wx.MenuBar.__init__(self, *args, **kwds)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyMenuBar.__set_properties
        pass
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyMenuBar.__do_layout
        pass
        # end wxGlade

# end of class MyMenuBar

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.ButtonIDDict = {}
        self.RPCMethodDict = {}
        self.Server = None
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        #make all the static boxes...
        self.bssbRegRPCs_staticbox = wx.StaticBox(self, -1, "Registered RPCs")
        self.bsvCmdFifoRPCs_staticbox = wx.StaticBox(self, -1, "CmdFIFO RPCs")
        self.bshServerInfo_staticbox = wx.StaticBox(self, -1, "Server Information")
        self.bsTransactions_staticbox = wx.StaticBox(self, -1, "Transactions")

        #make the scroll window to contain the buttons per server rpc...
        self.swRegRPCs = wx.ScrolledWindow(self, -1, style=wx.TAB_TRAVERSAL)

        #make and fill the cmdType choice...
        choiceList = CmdTypeChoicesDict.keys()
        choiceList.sort()
        self.choice_1 = wx.Choice(self, -1, choices=choiceList)

        #Make the buttons that will call core CmdFIFO RPCs...
        self.btnGetName        = wx.Button(self, -1, "Get Server Name")
        self.btnGetDescription = wx.Button(self, -1, "Get Server Desc")
        self.btnGetVersion     = wx.Button(self, -1, "Get Server Version")
        self.btnGetQueueLength = wx.Button(self, -1, "Get Queue Length")
        self.btnEnableLogging  = wx.Button(self, -1, "Enable Logging")
        self.btnDisableLogging = wx.Button(self, -1, "Disable Logging")
        self.btnPingFIFO       = wx.Button(self, -1, "Ping FIFO")
        self.btnPingDispatcher = wx.Button(self, -1, "Ping Dispatcher")
        self.btnShowFIFOGUI    = wx.Button(self, -1, "Show FIFO GUI")
        self.btnHideFIFOGUI    = wx.Button(self, -1, "Hide FIFO GUI")
        self.btnGetProcessID   = wx.Button(self, -1, "Get Process ID")
        self.btnStopServer     = wx.Button(self, -1, "Stop Server")
        self.btnKillServer     = wx.Button(self, -1, "Kill Server")
        self.btnDebugDelay     = wx.Button(self, -1, "Debug Delay")

        self.Bind(wx.EVT_BUTTON, self.OnGetNameClick, self.btnGetName)
        self.Bind(wx.EVT_BUTTON, self.OnGetDescriptionClick, self.btnGetDescription)
        self.Bind(wx.EVT_BUTTON, self.OnGetVersionClick, self.btnGetVersion)
        self.Bind(wx.EVT_BUTTON, self.OnGetQueueLengthClick, self.btnGetQueueLength)
        self.Bind(wx.EVT_BUTTON, self.OnShowFIFOGUIClick, self.btnShowFIFOGUI)
        self.Bind(wx.EVT_BUTTON, self.OnHideFIFOGUIClick, self.btnHideFIFOGUI)
        self.Bind(wx.EVT_BUTTON, self.OnEnableLoggingClick, self.btnEnableLogging)
        self.Bind(wx.EVT_BUTTON, self.OnDisableLoggingClick, self.btnDisableLogging)
        self.Bind(wx.EVT_BUTTON, self.OnGetProcessIDClick, self.btnGetProcessID)
        self.Bind(wx.EVT_BUTTON, self.OnStopServerClick, self.btnStopServer)
        self.Bind(wx.EVT_BUTTON, self.OnKillServerClick, self.btnKillServer)
        self.Bind(wx.EVT_BUTTON, self.OnPingFIFOClick, self.btnPingFIFO)
        self.Bind(wx.EVT_BUTTON, self.OnPingDispatcherClick, self.btnPingDispatcher)
        self.Bind(wx.EVT_BUTTON, self.OnDebugDelayClick, self.btnDebugDelay)

        self.lblServerName = wx.StaticText(self, -1, "Name:")
        self.tlblServerName = wx.StaticText(self, -1, "---")
        self.lblProxyAddress = wx.StaticText(self, -1, "Address:")
        self.tlblProxyAddress = wx.StaticText(self, -1, "---")
        self.lblProxyPort = wx.StaticText(self, -1, "Port:")
        self.tlblProxyPort = wx.StaticText(self, -1, "---")

        self.text_ctrl_1 = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE+wx.HSCROLL)

        self.__set_properties()
        self.__do_layout()
          # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("CmdFIFO Test Client")
        self.choice_1.SetSelection(2)
        self.swRegRPCs.SetScrollRate(10, 10)
        self.swRegRPCs.SetSize((-1, 200))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MyFrame.__do_layout

        #Make the sizers...
        bshMain = wx.BoxSizer(wx.HORIZONTAL)
        bsvMain01 = wx.BoxSizer(wx.VERTICAL)
        bsTransactions = wx.StaticBoxSizer(self.bsTransactions_staticbox, wx.VERTICAL)
        bshServerInfo = wx.StaticBoxSizer(self.bshServerInfo_staticbox, wx.HORIZONTAL)
        bsvButtonGroups = wx.BoxSizer(wx.VERTICAL)
        bsvCmdFifoRPCs = wx.StaticBoxSizer(self.bsvCmdFifoRPCs_staticbox, wx.VERTICAL)
        bssbRegRPCs = wx.StaticBoxSizer(self.bssbRegRPCs_staticbox, wx.VERTICAL)

        #Fill the 'registered rpc' ScrollingWindow and StaticBoxSizer...
        #bsvRPCButtonContainer = wx.BoxSizer(wx.VERTICAL)
        #bsvRPCButtonContainer.Add(self.button_3, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #bsvRPCButtonContainer.Add(self.button_4, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #bsvRPCButtonContainer.Add(self.button_5, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #bsvRPCButtonContainer.Add(self.button_6, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #bsvRPCButtonContainer.Add(self.button_7, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #self.swRegRPCs.SetAutoLayout(True)
        #self.swRegRPCs.SetSizer(bsvRPCButtonContainer)
        #bsvRPCButtonContainer.Fit(self.swRegRPCs)
        #bsvRPCButtonContainer.SetSizeHints(self.swRegRPCs)

        #Add the choice and ScrollingWindow (containing the sizer with buttons in it) to the RegRPCs sizer...
        bssbRegRPCs.Add(self.choice_1, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bssbRegRPCs.Add(self.swRegRPCs, 1, wx.EXPAND, 0)

        #Fill up the CmdFIFO buttons sizer...
        bsvCmdFifoRPCs.Add(self.btnGetName, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnGetDescription, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnGetVersion, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnGetQueueLength, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnEnableLogging, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnDisableLogging, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnPingFIFO, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnPingDispatcher, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnShowFIFOGUI, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnHideFIFOGUI, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnGetProcessID, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnStopServer, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnKillServer, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        bsvCmdFifoRPCs.Add(self.btnDebugDelay, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        #Now stuff what will be the left side of the main sizer (the
        #registered RPC call buttons and the core buttons)...
        bsvButtonGroups.Add(bssbRegRPCs, 1, wx.EXPAND, 0)
        bsvButtonGroups.Add(bsvCmdFifoRPCs, 0, wx.EXPAND, 0)

        #Now stuff the ServerInfo sizer...
        bshServerInfo.Add(self.lblServerName, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bshServerInfo.Add(self.tlblServerName, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bshServerInfo.Add(self.lblProxyAddress, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bshServerInfo.Add(self.tlblProxyAddress, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bshServerInfo.Add(self.lblProxyPort, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)
        bshServerInfo.Add(self.tlblProxyPort, 0, wx.ALL|wx.ADJUST_MINSIZE, 5)

        #Stuff the Transaction sizer...
        bsTransactions.Add(self.text_ctrl_1, 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        #Now stuff what will be the right side of the main sizer...
        bsvMain01.Add(bshServerInfo, 0, wx.EXPAND|wx.ALL, 3)
        bsvMain01.Add(bsTransactions, 1, wx.EXPAND|wx.ALL, 3)

        #Stuff the main sizer...
        bshMain.Add(bsvButtonGroups, 0, wx.EXPAND, 0)
        bshMain.Add(bsvMain01, 1, wx.EXPAND, 0)

        self.SetAutoLayout(True)
        self.SetSizer(bshMain)
        bshMain.Fit(self)
        bshMain.SetSizeHints(self)
        self.Layout()
        # end wxGlade

    def CreateRPCButtons(self, rpcMethodDict):
        "Dynamically creates buttons in 'registered rpc' window."
        assert isinstance(rpcMethodDict, dict) #for Wing
        self.RPCMethodDict = rpcMethodDict
        bsvRPCButtonContainer = wx.BoxSizer(wx.VERTICAL)
        i=0
        methods = rpcMethodDict.keys()
        methods.sort()
        for methodName in methods:
            if (methodName.find("system.") < 0) and (methodName.find("CmdFIFO.") < 0):
                i += 1
                btnName = "btnRPC%s" % i
                btn = wx.Button(self.swRegRPCs, -1, "  " + methodName, style = wx.BU_LEFT)
                self.__setattr__(btnName, btn)
                bsvRPCButtonContainer.Add(self.__getattribute__(btnName), 0, \
                                          wx.EXPAND|wx.ADJUST_MINSIZE|wx.RIGHT, 25)
                self.ButtonIDDict.setdefault(str(btn.GetId()),methodName)
                self.Bind(wx.EVT_BUTTON, self.OnRPCButtonClick, btn)
                toolTip = self.Server.system.methodHelp(methodName)
                btn.SetToolTipString(toolTip)

        self.swRegRPCs.SetAutoLayout(True)
        self.swRegRPCs.SetSizer(bsvRPCButtonContainer)
        bsvRPCButtonContainer.Fit(self.swRegRPCs)
        bsvRPCButtonContainer.SetSizeHints(self.swRegRPCs)

    def _GetArgsFromDialog(self, FuncName, Args):
        argsOkay = True
        argTuple = None
        dlg = wx.TextEntryDialog(
                self, "The selected RPC function requires arguments of the form:"
                      "\n\n%s\n\n"
                      "Please enter the arguments below as if you were calling\n"
                      "the function in a Python shell (without outside parentheses)." % Args,
                FuncName, '')
        if dlg.ShowModal() != wx.ID_OK:
            argsOkay = False
            dlg.Destroy()
        else:
            #make a tuple out of what gets entered...
            dlgValue = dlg.GetValue()
            dlg.Destroy()
            execStr = "argTuple = (" + dlgValue + ")"
            try:
                #security hole here since this executes code...
                exec(execStr)
            except Exception:
                argsOkay = False
                dlg = wx.MessageDialog(self, 'There was a problem with the typed arguments.\n\n'
                                              'Expected form: %s\n'
                                              'What you typed: %s\n\n'
                                              'The RPC call will not be executed.\n\n'
                                              'Possible problems:\n'
                                              '  - String args must be enclosed in quotes\n'
                                              '  - do not surround with brackets (unless sending a tuple)' % (Args, dlgValue),
                                       'Error with arguments!',
                                       wx.OK | wx.ICON_ERROR
                                       #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                       )
                dlg.ShowModal()
                dlg.Destroy()
            else:
                if not isinstance(argTuple, tuple):
                    argTuple = (argTuple, )
        if argsOkay == False:
            argTuple = None
        return argTuple

    def _InvokeRPC(self, FuncName, ArgTuple):
        assert isinstance(ArgTuple,tuple)
        assert isinstance(self.Server, CmdFIFO.CmdFIFOServerProxy)
        argStr = ", ".join([repr(x) for x in ArgTuple])
        self.text_ctrl_1.AppendText("Calling function: %s(%s)\n" % (FuncName, argStr))
        try:
            ret = self.Server.__getattr__(FuncName)(*ArgTuple)
        except Exception, E:
            self.text_ctrl_1.AppendText("  Exception raised: %s\n" % E)
        else:
            self.text_ctrl_1.AppendText("  Response = %r\n" % ret)

    def OnRPCButtonClick(self, event):
        assert isinstance(self.Server, CmdFIFO.CmdFIFOServerProxy)
        #figure out what to call...
        funcName = self.ButtonIDDict[str(event.GetId())]
        #set function method to what is in the choice box
        choiceStr = self.choice_1.GetStringSelection()
        funcMethod = CmdTypeChoicesDict[choiceStr]
        if funcMethod == CmdFIFO.CMD_TYPE_Callback:
            self.Server.SetFunctionMode(funcName, funcMethod, self.CallbackTest)
        else:
            self.Server.SetFunctionMode(funcName, funcMethod)
        #if args exist, prompt for this...
        args = self.RPCMethodDict[funcName]
        if args == '':
            argTuple = ()
        else:
            #need to ask user for the argTuple to invoke the function...
            argTuple = self._GetArgsFromDialog(funcName, args)
        if argTuple != None:
            self._InvokeRPC(funcName, argTuple)

    def OnGetNameClick(self, event):
        self._InvokeRPC('CmdFIFO.GetName', ())
    def OnGetDescriptionClick(self, event):
        self._InvokeRPC('CmdFIFO.GetDescription', ())
    def OnGetVersionClick(self, event):
        self._InvokeRPC('CmdFIFO.GetVersion', ())
    def OnGetQueueLengthClick(self, event):
        self._InvokeRPC('CmdFIFO.GetQueueLength', ())
    def OnPingFIFOClick(self, event):
        self._InvokeRPC('CmdFIFO.PingFIFO', ())
    def OnPingDispatcherClick(self, event):
        self._InvokeRPC('CmdFIFO.PingDispatcher', ())
    def OnShowFIFOGUIClick(self, event):
        self._InvokeRPC('CmdFIFO.ShowGUI', ())
    def OnShowFIFOGUIClick(self, event):
        self._InvokeRPC('CmdFIFO.ShowGUI', ())
    def OnHideFIFOGUIClick(self, event):
        self._InvokeRPC('CmdFIFO.HideGUI', ())
    def OnEnableLoggingClick(self, event):
        self._InvokeRPC('CmdFIFO.SetLoggingStatus', (True,))
    def OnDisableLoggingClick(self, event):
        self._InvokeRPC('CmdFIFO.SetLoggingStatus', (False,))
    def OnGetProcessIDClick(self, event):
        self._InvokeRPC('CmdFIFO.GetProcessID', ())
    def OnStopServerClick(self, event):
        dlg = wx.SingleChoiceDialog(self, 'Are you sure?','Are you sure?',['Yes','No'], wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            if dlg.GetStringSelection() == 'Yes':
                self._InvokeRPC('CmdFIFO.StopServer', ())
        dlg.Destroy()
    def OnKillServerClick(self, event):
        dlg = wx.TextEntryDialog(self,
                  "Killing the server requires a password to confirm the kill.\n\nPlease enter the password now (no quotes required):",
                  "Kill Server Confirmation","")
        if dlg.ShowModal() == wx.ID_OK:
            pwd = dlg.GetValue()
            if pwd != "":
                self._InvokeRPC('CmdFIFO.KillServer',(pwd,))
        dlg.Destroy()

    def OnDebugDelayClick(self, event):
        argTuple = self._GetArgsFromDialog("CmdFIFO.DebugDelay", "DelayTime_s")
        if argTuple != None:
            self._InvokeRPC('CmdFIFO.DebugDelay', argTuple)

    def CallbackTest(self, ReturnedVars, Fault):
        self.text_ctrl_1.AppendText("  *** Callback received.  Ret = %r  Fault = %r\n" %(ReturnedVars,Fault))


# end of class MyFrame

def PrintUsage():
    print HELP_STRING

def main():
    try:

        import sys
        import exceptions
        import getopt

        try:
            options, args = getopt.getopt(
                                      sys.argv[1:],
                                      'a:p:c:hs',
                                      ['serveraddr=', 'serverport=', 'callbackaddr=', 'help', '--simple']
                                         )
        except getopt.GetoptError, e:
            print e
            sys.exit(1)

        proxyAddress="127.0.0.1"
        proxyPort=8001
        callbackServerAddress = 8002 #default
        simpleMode = False
        for o, a in options:
            if o in ['-h', '--help']:
                PrintUsage()
                sys.exit()
            if o in ['-a', '--serveraddr']:
                proxyAddress = a
            if o in ['-p', '--serverport']:
                proxyPort = a
            if o in ['-c', '--callbackaddr']:
                callbackServerAddress = a
            if o in ['-s', '--simple']:
                simpleMode = True

        # ########
        #Set up the server proxy...
        serverURL = "http://%s:%s" % (proxyAddress, proxyPort)
        print "***************"
        print "Configuring connection to server at '%s'" % serverURL
        print "***************"
        try:
            server = CmdFIFO.CmdFIFOServerProxy(uri = serverURL, \
                                IsDontCareConnection = False,
                                ClientName = "TestClient", CallbackURI = "http://localhost:" + str(callbackServerAddress))
            #reconfigure the default on some functions...
            #server.SetFunctionMode("Delay",CmdFIFO.CMD_TYPE_Callback, CallbackTest)
            #grab a list of the supported methods...
            if not simpleMode:
                rpcMethodList = server.system.listMethods()
                #Now build up a dictionary with the keys as method names and values as strings
                #describing the args...
                rpcDict = {}
                for method in rpcMethodList:
                    sig = server.system.methodSignature(method)
                    assert isinstance(sig, str)
                    #strip the self arg if a method...
                    sig = sig.replace("(self,","(",1)
                    sig = sig.replace("(self)","",1)
                    rpcDict.setdefault(method, sig)
                #print "RPCDict = ", repr(rpcDict)
                if len(rpcDict) == 0:
                    sys.exit()

        except Exception, E:
            print "Trapped an exception when connecting to server:", E

        else:
            app = wx.PySimpleApp(0)
            wx.InitAllImageHandlers()
            frame_1 = MyFrame(None, -1, "")
            #attach the server to the frame (bad code, but anyway)...
            frame_1.Server=server
            #Set some visuals...
            frame_1.tlblServerName.SetLabel(server.CmdFIFO.GetName())
            frame_1.tlblProxyAddress.SetLabel(proxyAddress)
            frame_1.tlblProxyPort.SetLabel(str(proxyPort))
            #set up a listening server (for callbacks)...
            callbackServer = CmdFIFO.CmdFIFOSimpleCallbackServer(("localhost",callbackServerAddress),CallbackList=(frame_1.CallbackTest,))
            callbackServer.Launch()
            if not simpleMode:
                #Now autogenerate some buttons...
                frame_1.CreateRPCButtons(rpcDict)
            #frame_1.button_3 = wx.Button(self.swRegRPCs, -1, "button_3")
            app.SetTopWindow(frame_1)
            frame_1.Show()
            app.MainLoop()
            callbackServer.Server._CmdFIFO_StopServer()
            pass
    except Exception, E:
        raise E
#    if not isinstance(E, SystemExit):
#      BetterTraceback.print_exc_plus()

if __name__ == "__main__":
    main()