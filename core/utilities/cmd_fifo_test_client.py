"""This executable script provides a generic GUI for accessing all applications
that use CmdFIFO server.

All available RPC calls are available (with help in the form of docstrings for
each).

In addition, all core CmdFIFO calls are available.

For instructions on how to use, use the -h command line switch to get:

P.S. This is a QT based implementation of the previously WX based script.
"""
import CmdFIFO

from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGroupBox, QTextEdit, QHBoxLayout, \
    QVBoxLayout, QPushButton, QMessageBox, QInputDialog, QComboBox, QScrollArea, QFrame
from PyQt5 import QtCore

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

CmdTypeChoicesDict = {
    "CMD_TYPE_Default": CmdFIFO.CMD_TYPE_Default,
    "CMD_TYPE_Blocking": CmdFIFO.CMD_TYPE_Blocking,
    "CMD_TYPE_VerifyOnly": CmdFIFO.CMD_TYPE_VerifyOnly,
    "CMD_TYPE_Callback": CmdFIFO.CMD_TYPE_Callback,
}


def PrintUsage():
    print(HELP_STRING)


class TestClientWidget(QWidget):
    def __init__(self, parent=None):
        super(TestClientWidget, self).__init__(parent)
        self.mgl = QHBoxLayout()
        self.initGUI()
        self.setLayout(self.mgl)
        return

    def initGUI(self):
        # Initiate all GUI
        self.__init_items()
        self.__init_layouts()
        self.__set_layouts()
        self.__add_widgets()
        self.__init_core_rpc_buttons()
        self.__init_server_labels()
        self.__set_properties()
        return self.mgl

    def __init_items(self):
        # initiate all the items: qboxes, qtext, qframe
        self.choice_1 = QComboBox()
        self.text_ctrl_1 = QTextEdit()
        self.leftPart = QGroupBox()
        self.rightPart = QGroupBox()
        self.RegisteredRPCsWidget = QGroupBox("Registered RPCs")
        self.RegisteredRPCs = QFrame()
        self.RegisteredRPCsWidgetScrollable = QScrollArea()
        self.CmdFIFORPSWidget = QGroupBox("CmdFIFO RPCs")
        self.ServerInformationWidget = QGroupBox("Server Information")
        self.TransactionsWidget = QGroupBox("Transactions")

    def __init_layouts(self):
        # initiate all the layouts
        self.leftPartLayout = QVBoxLayout()
        self.rightPartLayout = QVBoxLayout()
        self.RegisteredRPCsWidgetLayout = QVBoxLayout()
        self.RegisteredRPCsLayout = QVBoxLayout()
        self.CmdFIFORPSWidgetLayout = QVBoxLayout()
        self.ServerInformationWidgetLayout = QHBoxLayout()
        self.TransactionsWidgetLayout = QHBoxLayout()

    def __set_layouts(self):
        # apply all the layouts to corresponded boxes
        self.RegisteredRPCsWidget.setLayout(self.RegisteredRPCsWidgetLayout)
        self.RegisteredRPCs.setLayout(self.RegisteredRPCsLayout)
        self.CmdFIFORPSWidget.setLayout(self.CmdFIFORPSWidgetLayout)
        self.ServerInformationWidget.setLayout(
            self.ServerInformationWidgetLayout)
        self.TransactionsWidget.setLayout(self.TransactionsWidgetLayout)
        self.leftPart.setLayout(self.leftPartLayout)
        self.rightPart.setLayout(self.rightPartLayout)
        self.RegisteredRPCsWidgetScrollable.setWidget(
            self.RegisteredRPCs)

    def __add_widgets(self):
        # add all the widgets to the layouts
        self.mgl.addWidget(self.leftPart)
        self.mgl.addWidget(self.rightPart)
        self.TransactionsWidgetLayout.addWidget(self.text_ctrl_1)
        self.RegisteredRPCsWidgetLayout.addWidget(self.choice_1)
        self.RegisteredRPCsWidgetLayout.addWidget(self.RegisteredRPCsWidgetScrollable)

        self.leftPartLayout.addWidget(self.RegisteredRPCsWidget)
        self.leftPartLayout.addWidget(self.CmdFIFORPSWidget)
        self.rightPartLayout.addWidget(self.ServerInformationWidget)
        self.rightPartLayout.addWidget(self.TransactionsWidget)

    def __set_properties(self):
        # set some properties
        self.setWindowTitle("CmdFIFO Test Client")
        choiceList = list(CmdTypeChoicesDict.keys())
        choiceList.sort()
        self.choice_1.addItems(choiceList)
        self.choice_1.setCurrentIndex(2)
        self.leftPart.setFixedWidth(250)
        self.RegisteredRPCsWidgetScrollable.setWidgetResizable(True)
        self.text_ctrl_1.setReadOnly(True)

        self.ServerInformationWidgetLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.RegisteredRPCsWidgetLayout.setAlignment(QtCore.Qt.AlignTop)

    def __init_core_rpc_buttons(self):
        # init the buttons that will call core CmdFIFO RPCs...
        self.btnGetName = QPushButton("Get Server Name")
        self.btnGetDescription = QPushButton("Get Server Desc")
        self.btnGetVersion = QPushButton("Get Server Version")
        self.btnGetQueueLength = QPushButton("Get Queue Length")
        self.btnEnableLogging = QPushButton("Enable Logging")
        self.btnDisableLogging = QPushButton("Disable Logging")
        self.btnPingFIFO = QPushButton("Ping FIFO")
        self.btnPingDispatcher = QPushButton("Ping Dispatcher")
        self.btnShowFIFOGUI = QPushButton("Show FIFO GUI")
        self.btnHideFIFOGUI = QPushButton("Hide FIFO GUI")
        self.btnGetProcessID = QPushButton("Get Process ID")
        self.btnStopServer = QPushButton("Stop Server")
        self.btnKillServer = QPushButton("Kill Server")
        self.btnDebugDelay = QPushButton("Debug Delay")

        # bind buttons to functions
        self.btnGetName.clicked.connect(self.OnGetNameClick)
        self.btnGetDescription.clicked.connect(self.OnGetDescriptionClick)
        self.btnGetVersion.clicked.connect(self.OnGetVersionClick)
        self.btnGetQueueLength.clicked.connect(self.OnGetQueueLengthClick)
        self.btnShowFIFOGUI.clicked.connect(self.OnShowFIFOGUIClick)
        self.btnHideFIFOGUI.clicked.connect(self.OnHideFIFOGUIClick)
        self.btnEnableLogging.clicked.connect(self.OnEnableLoggingClick)
        self.btnDisableLogging.clicked.connect(self.OnDisableLoggingClick)
        self.btnGetProcessID.clicked.connect(self.OnGetProcessIDClick)
        self.btnStopServer.clicked.connect(self.OnStopServerClick)
        self.btnKillServer.clicked.connect(self.OnKillServerClick)
        self.btnPingFIFO.clicked.connect(self.OnPingFIFOClick)
        self.btnPingDispatcher.clicked.connect(self.OnPingDispatcherClick)
        self.btnDebugDelay.clicked.connect(self.OnDebugDelayClick)

        # add buttons to the CmdFIFORPSWidgetLayout
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnGetName)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnGetDescription)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnGetVersion)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnGetQueueLength)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnEnableLogging)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnDisableLogging)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnPingFIFO)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnPingDispatcher)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnShowFIFOGUI)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnHideFIFOGUI)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnGetProcessID)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnStopServer)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnKillServer)
        self.CmdFIFORPSWidgetLayout.addWidget(self.btnDebugDelay)

    def __init_server_labels(self):
        self.lblServerName = QLabel("Name:")
        self.tlblServerName = QLabel("---")
        self.lblProxyAddress = QLabel("Address:")
        self.tlblProxyAddress = QLabel("---")
        self.lblProxyPort = QLabel("Port:")
        self.tlblProxyPort = QLabel("---")

        self.ServerInformationWidgetLayout.addWidget(self.lblServerName)
        self.ServerInformationWidgetLayout.addWidget(self.tlblServerName)
        self.ServerInformationWidgetLayout.addWidget(self.lblProxyAddress)
        self.ServerInformationWidgetLayout.addWidget(self.tlblProxyAddress)
        self.ServerInformationWidgetLayout.addWidget(self.lblProxyPort)
        self.ServerInformationWidgetLayout.addWidget(self.tlblProxyPort)

    def _InvokeRPC(self, FuncName, ArgTuple, KwArgDict={}):
        assert isinstance(ArgTuple, tuple)
        assert isinstance(KwArgDict, dict)
        assert isinstance(self.Server, CmdFIFO.CmdFIFOServerProxy)
        argStr = ", ".join([repr(x) for x in ArgTuple])
        if KwArgDict:
            if argStr:
                argStr += ", "
            argStr += ", ".join([f"{k}={repr(v)}" for k,
                                 v in KwArgDict.items()])
        self.text_ctrl_1.append(f"Calling function: {FuncName}({argStr})\n")
        try:
            ret = self.Server.__getattr__(FuncName)(*ArgTuple, **KwArgDict)
        except Exception as E:
            self.text_ctrl_1.append(f"  Exception raised: {E}\n")
        else:
            self.text_ctrl_1.append(f"  Response = {ret}\n")

    def OnGetNameClick(self):
        self._InvokeRPC('CmdFIFO.GetName', ())

    def OnGetDescriptionClick(self):
        self._InvokeRPC('CmdFIFO.GetDescription', ())

    def OnGetVersionClick(self):
        self._InvokeRPC('CmdFIFO.GetVersion', ())

    def OnGetQueueLengthClick(self):
        self._InvokeRPC('CmdFIFO.GetQueueLength', ())

    def OnShowFIFOGUIClick(self):
        self._InvokeRPC('CmdFIFO.ShowGUI', ())

    def OnHideFIFOGUIClick(self):
        self._InvokeRPC('CmdFIFO.HideGUI', ())

    def OnEnableLoggingClick(self):
        self._InvokeRPC('CmdFIFO.SetLoggingStatus', (True, ))

    def OnDisableLoggingClick(self):
        self._InvokeRPC('CmdFIFO.SetLoggingStatus', (False, ))

    def OnGetProcessIDClick(self):
        self._InvokeRPC('CmdFIFO.GetProcessID', ())

    def OnPingFIFOClick(self):
        self._InvokeRPC('CmdFIFO.PingFIFO', ())

    def OnPingDispatcherClick(self):
        self._InvokeRPC('CmdFIFO.PingDispatcher', ())

    def OnStopServerClick(self):
        dlg = QMessageBox()
        dlg.setText("Are you sure?")
        dlg.setWindowTitle("Are you sure?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = dlg.exec_()
        if retval == QMessageBox.Yes:
            self._InvokeRPC('CmdFIFO.StopServer', ())

    def OnKillServerClick(self):
        text, ok = QInputDialog.getText(
            self, "Kill Server Confirmation", "Killing the server requires a password to confirm the kill.\n\n"
            "Please enter the password now (no quotes required):")
        if ok and text != "":
            self._InvokeRPC('CmdFIFO.KillServer', (text, ))

    def OnDebugDelayClick(self):
        args, kwargs = self._GetArgsFromDialog(
            "CmdFIFO.DebugDelay", "DelayTime_s")
        if args is not None:
            self._InvokeRPC('CmdFIFO.DebugDelay', args, kwargs)

    def _GetArgsFromDialog(self, FuncName, Args):
        argsOkay = True
        args = ()
        kwargs = {}
        text, ok = QInputDialog.getText(self, FuncName, "The selected RPC function requires arguments of the form:"
                                        f"\n\n{Args}\n\n"
                                        "Please enter the arguments below as if you were calling\n"
                                        "the function in a Python shell (without outside parentheses).")
        if not ok:
            argsOkay = False
        else:
            # make a tuple out of what gets entered...
            dlgValue = text
            try:
                # This is required for test_client to pass anything than
                # integers or strings
                def my_wrapper(*args, **kwargs):
                    return args, kwargs

                command_to_eval = "my_wrapper(" + dlgValue + ")"
                args, kwargs = eval(command_to_eval)
            except Exception as e:
                print(e)
                argsOkay = False

                dlg = QMessageBox()
                dlg.setText('There was a problem with the typed arguments.\n\n'
                            f'Expected form: {Args}\n'
                            f'What you typed: {dlgValue}\n\n'
                            'The RPC call will not be executed.\n\n'
                            'Possible problems:\n'
                            '  - String args must be enclosed in quotes\n'
                            '  - do not surround with brackets (unless sending a tuple)')
                dlg.setWindowTitle('Error with arguments!')
                dlg.setStandardButtons(QMessageBox.Ok)
                dlg.exec_()
            else:
                if not isinstance(args, tuple):
                    args = (args, )
        if not argsOkay:
            args = None
        return args, kwargs

    def CallbackTest(self, ReturnedVars, Fault):
        self.text_ctrl_1.append(
            f"  *** Callback received.  Ret = {ReturnedVars}  Fault = {Fault}\n")

    def OnRPCButtonClick(self):
        assert isinstance(self.Server, CmdFIFO.CmdFIFOServerProxy)
        # figure out what to call...
        sender = self.sender()
        funcName = sender.__getattribute__("method_name")
        # set function method to what is in the choice box
        choiceStr = self.choice_1.currentText()
        funcMethod = CmdTypeChoicesDict[choiceStr]
        if funcMethod == CmdFIFO.CMD_TYPE_Callback:
            self.Server.SetFunctionMode(
                funcName, funcMethod, self.CallbackTest)
        else:
            self.Server.SetFunctionMode(funcName, funcMethod)
        # if args exist, prompt for this...
        args = self.RPCMethodDict[funcName]
        if args == '()':
            args = ()
            kwargs = {}
        else:
            # need to ask user for the argTuple to invoke the function...
            args, kwargs = self._GetArgsFromDialog(funcName, args)
        if args is not None:
            self._InvokeRPC(funcName, args, kwargs)

    def CreateRPCButtons(self, rpcMethodDict):
        """
            Dynamically creates buttons in 'registered rpc' window.
        """
        assert isinstance(rpcMethodDict, dict)
        self.RPCMethodDict = rpcMethodDict
        i = 0
        methods = list(rpcMethodDict.keys())
        methods.sort()
        self.RPCButtons = []
        for methodName in methods:
            if (methodName.find("system.") < 0) and (methodName.find("CmdFIFO.") < 0):
                i += 1
                btn = QPushButton(f"  {methodName}")
                btn.clicked.connect(self.OnRPCButtonClick)
                btn.__setattr__("method_name", methodName)
                self.RegisteredRPCsLayout.addWidget(btn)
                self.RPCButtons.append(btn)
                toolTip = self.Server.system.methodHelp(methodName)
                btn.setToolTip(toolTip)


def main():
    try:

        import sys
        # import exceptions
        import getopt

        try:
            options, args = getopt.getopt(sys.argv[1:], 'a:p:c:hs',
                                          ['serveraddr=', 'serverport=', 'callbackaddr=', 'help', '--simple'])
        except getopt.GetoptError as e:
            print(e)
            sys.exit(1)

        proxyAddress = "127.0.0.1"
        proxyPort = 8001
        callbackServerAddress = 8002  # default
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
                callbackServerAddress = int(a)
            if o in ['-s', '--simple']:
                simpleMode = True

        #########
        # Set up the server proxy...
        serverURL = f"http://{proxyAddress}:{proxyPort}"
        print("***************")
        print(f"Configuring connection to server at '{serverURL}'")
        print("***************")
        try:
            server = CmdFIFO.CmdFIFOServerProxy(uri=serverURL,
                                                IsDontCareConnection=False,
                                                ClientName="TestClient",
                                                CallbackURI="http://localhost:" + str(callbackServerAddress))
            # reconfigure the default on some functions...
            # server.SetFunctionMode("Delay",CmdFIFO.CMD_TYPE_Callback, CallbackTest)
            # grab a list of the supported methods...
            if not simpleMode:
                rpcMethodList = server.system.listMethods()
                # Now build up a dictionary with the keys as method names and values as strings
                # describing the args...
                rpcDict = {}
                for method in rpcMethodList:
                    sig = str(server.system.methodSignature(method))
                    # strip the self arg if a method...
                    sig = sig.replace("(self,", "(", 1)
                    sig = sig.replace("(self)", "()", 1)
                    rpcDict.setdefault(method, sig)
                if len(rpcDict) == 0:
                    sys.exit()

        except Exception as E:
            print("Trapped an exception when connecting to server:", E)

        else:
            app = QApplication([])

            window = TestClientWidget()
            window.Server = server

            window.tlblServerName.setText(server.CmdFIFO.GetName())
            window.tlblProxyAddress.setText(proxyAddress)
            window.tlblProxyPort.setText(str(proxyPort))

            callbackServer = CmdFIFO.CmdFIFOSimpleCallbackServer(("localhost", callbackServerAddress),
                                                                 CallbackList=(window.CallbackTest, ))
            callbackServer.Launch()

            if not simpleMode:
                # Now autogenerate some buttons...
                window.CreateRPCButtons(rpcDict)

            window.resize(960, 720)
            window.show()
            app.exec_()
    except Exception as E:
        raise E


if __name__ == "__main__":
    main()
