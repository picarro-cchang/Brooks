"""This executable script provides a generic GUI for accessing all applications
that use CmdFIFO server.

All available RPC calls are available (with help in the form of docstrings for
each).

In addition, all core CmdFIFO calls are available.

For instructions on how to use, use the -h command line switch to get:

P.S. This is a QT based implementation of the previously WX based script.
"""
import getopt
import sys

from qtpy import QtCore
from qtpy.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton,
                            QScrollArea, QTextEdit, QVBoxLayout, QWidget)

import CmdFIFO

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
        self.cmd_type_drop_list = QComboBox()
        self.log_text_box = QTextEdit()
        self.left_column_interface = QGroupBox()
        self.right_column_interface = QGroupBox()
        self.registered_rpcs_widget = QGroupBox("Registered RPCs")
        self.registered_rpcs = QFrame()
        self.registered_rpcs_widget_scrollable = QScrollArea()
        self.cmd_fifo_rpc_widget = QGroupBox("CmdFIFO RPCs")
        self.server_information_widget = QGroupBox("Server Information")
        self.transactions_widget = QGroupBox("Transactions")

    def __init_layouts(self):
        # initiate all the layouts
        self.left_column_interface_layout = QVBoxLayout()
        self.right_column_interface_layout = QVBoxLayout()
        self.registered_rpcs_widget_layout = QVBoxLayout()
        self.registered_rpcs_layout = QVBoxLayout()
        self.cmd_fifo_rpc_widget_layout = QVBoxLayout()
        self.server_information_widget_layout = QHBoxLayout()
        self.transactions_widget_layout = QHBoxLayout()

    def __set_layouts(self):
        # apply all the layouts to corresponded boxes
        self.registered_rpcs_widget.setLayout(self.registered_rpcs_widget_layout)
        self.registered_rpcs.setLayout(self.registered_rpcs_layout)
        self.cmd_fifo_rpc_widget.setLayout(self.cmd_fifo_rpc_widget_layout)
        self.server_information_widget.setLayout(self.server_information_widget_layout)
        self.transactions_widget.setLayout(self.transactions_widget_layout)
        self.left_column_interface.setLayout(self.left_column_interface_layout)
        self.right_column_interface.setLayout(self.right_column_interface_layout)
        self.registered_rpcs_widget_scrollable.setWidget(self.registered_rpcs)

    def __add_widgets(self):
        # add all the widgets to the layouts
        self.mgl.addWidget(self.left_column_interface)
        self.mgl.addWidget(self.right_column_interface)
        self.transactions_widget_layout.addWidget(self.log_text_box)
        self.registered_rpcs_widget_layout.addWidget(self.cmd_type_drop_list)
        self.registered_rpcs_widget_layout.addWidget(self.registered_rpcs_widget_scrollable)

        self.left_column_interface_layout.addWidget(self.registered_rpcs_widget)
        self.left_column_interface_layout.addWidget(self.cmd_fifo_rpc_widget)
        self.right_column_interface_layout.addWidget(self.server_information_widget)
        self.right_column_interface_layout.addWidget(self.transactions_widget)

    def __set_properties(self):
        # set some properties
        self.setWindowTitle("CmdFIFO Test Client")
        choice_list = list(CmdTypeChoicesDict.keys())
        choice_list.sort()
        self.cmd_type_drop_list.addItems(choice_list)
        self.cmd_type_drop_list.setCurrentIndex(2)
        self.left_column_interface.setFixedWidth(250)
        self.registered_rpcs_widget_scrollable.setWidgetResizable(True)
        self.log_text_box.setReadOnly(True)

        self.server_information_widget_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.registered_rpcs_layout.setAlignment(QtCore.Qt.AlignTop)

    def __init_core_rpc_buttons(self):
        # init the buttons that will call core CmdFIFO RPCs...
        self.btn_get_name = QPushButton("Get Server Name")
        self.btn_get_description = QPushButton("Get Server Desc")
        self.btn_get_version = QPushButton("Get Server Version")
        self.btn_get_queue_length = QPushButton("Get Queue Length")
        self.btn_enable_logging = QPushButton("Enable Logging")
        self.btn_disable_logging = QPushButton("Disable Logging")
        self.btn_ping_fifo = QPushButton("Ping FIFO")
        self.btn_ping_dispatcher = QPushButton("Ping Dispatcher")
        self.btn_show_fifo_gui = QPushButton("Show FIFO GUI")
        self.btn_hide_fifo_gui = QPushButton("Hide FIFO GUI")
        self.btn_get_process_id = QPushButton("Get Process ID")
        self.btn_stop_server = QPushButton("Stop Server")
        self.btn_kill_server = QPushButton("Kill Server")
        self.btn_debug_delay = QPushButton("Debug Delay")

        # bind buttons to functions
        self.btn_get_name.clicked.connect(self.on_get_name_click)
        self.btn_get_description.clicked.connect(self.on_get_description_click)
        self.btn_get_version.clicked.connect(self.on_get_version_click)
        self.btn_get_queue_length.clicked.connect(self.on_get_queue_length_click)
        self.btn_show_fifo_gui.clicked.connect(self.on_show_fifo_gui_click)
        self.btn_hide_fifo_gui.clicked.connect(self.on_hide_fifo_gui_click)
        self.btn_enable_logging.clicked.connect(self.on_enable_logging_click)
        self.btn_disable_logging.clicked.connect(self.on_disable_logging_click)
        self.btn_get_process_id.clicked.connect(self.on_get_process_id_click)
        self.btn_stop_server.clicked.connect(self.on_stop_server_click)
        self.btn_kill_server.clicked.connect(self.on_kill_server_click)
        self.btn_ping_fifo.clicked.connect(self.on_ping_fifo_click)
        self.btn_ping_dispatcher.clicked.connect(self.on_ping_dispatcher_click)
        self.btn_debug_delay.clicked.connect(self.on_debug_delay_click)

        # add buttons to the cmd_fifo_rpc_widget_layout
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_name)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_description)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_version)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_queue_length)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_enable_logging)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_disable_logging)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_ping_fifo)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_ping_dispatcher)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_show_fifo_gui)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_hide_fifo_gui)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_process_id)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_stop_server)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_kill_server)
        self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_debug_delay)

    def __init_server_labels(self):
        self.server_name_label = QLabel("Name:")
        self.dynamic_server_name_label = QLabel("---")
        self.proxy_address_label = QLabel("Address:")
        self.dynamic_proxy_address_label = QLabel("---")
        self.proxy_port_label = QLabel("Port:")
        self.dynamic_proxy_port_label = QLabel("---")

        self.server_information_widget_layout.addWidget(self.server_name_label)
        self.server_information_widget_layout.addWidget(self.dynamic_server_name_label)
        self.server_information_widget_layout.addWidget(self.proxy_address_label)
        self.server_information_widget_layout.addWidget(self.dynamic_proxy_address_label)
        self.server_information_widget_layout.addWidget(self.proxy_port_label)
        self.server_information_widget_layout.addWidget(self.dynamic_proxy_port_label)

    def _invoke_rpc(self, func_name, arg_tuple, kw_arg_dict={}):
        if not isinstance(arg_tuple, tuple):
            raise ValueError(f"arg_tuple has to be tuple, got {type(arg_tuple)} instead.")
        if not isinstance(kw_arg_dict, dict):
            raise ValueError(f"kw_arg_dict has to be dict, got {type(kw_arg_dict)} instead.")
        if not isinstance(self.server, CmdFIFO.CmdFIFOServerProxy):
            raise ValueError(f"self.server has to be CmdFIFO.CmdFIFOServerProxy, got {type(self.server)} instead.")

        argStr = ", ".join([repr(x) for x in arg_tuple])
        if kw_arg_dict:
            if argStr:
                argStr += ", "
            argStr += ", ".join([f"{k}={repr(v)}" for k, v in kw_arg_dict.items()])
        self.log_text_box.append(f"Calling function: {func_name}({argStr})\n")
        QApplication.processEvents()
        try:
            ret = self.server.__getattr__(func_name)(*arg_tuple, **kw_arg_dict)
        except Exception as e:  # noqa
            # catch any exceptions on the server side.
            self.log_text_box.append(f"  Exception raised: {e}\n")
        else:
            self.log_text_box.append(f"  Response = {ret}\n")

    def on_get_name_click(self):
        self._invoke_rpc('CmdFIFO.GetName', ())

    def on_get_description_click(self):
        self._invoke_rpc('CmdFIFO.GetDescription', ())

    def on_get_version_click(self):
        self._invoke_rpc('CmdFIFO.GetVersion', ())

    def on_get_queue_length_click(self):
        self._invoke_rpc('CmdFIFO.GetQueueLength', ())

    def on_show_fifo_gui_click(self):
        self._invoke_rpc('CmdFIFO.ShowGUI', ())

    def on_hide_fifo_gui_click(self):
        self._invoke_rpc('CmdFIFO.HideGUI', ())

    def on_enable_logging_click(self):
        self._invoke_rpc('CmdFIFO.SetLoggingStatus', (True, ))

    def on_disable_logging_click(self):
        self._invoke_rpc('CmdFIFO.SetLoggingStatus', (False, ))

    def on_get_process_id_click(self):
        self._invoke_rpc('CmdFIFO.GetProcessID', ())

    def on_ping_fifo_click(self):
        self._invoke_rpc('CmdFIFO.PingFIFO', ())

    def on_ping_dispatcher_click(self):
        self._invoke_rpc('CmdFIFO.PingDispatcher', ())

    def on_stop_server_click(self):
        dlg = QMessageBox()
        dlg.setText("Are you sure?")
        dlg.setWindowTitle("Are you sure?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = dlg.exec_()
        if retval == QMessageBox.Yes:
            self._invoke_rpc('CmdFIFO.StopServer', ())

    def on_kill_server_click(self):
        text, ok = QInputDialog.getText(
            self, "Kill Server Confirmation", "Killing the server requires a password to confirm the kill.\n\n"
            "Please enter the password now (no quotes required):")
        if ok and text != "":
            self._invoke_rpc('CmdFIFO.KillServer', (text, ))

    def on_debug_delay_click(self):
        args, kwargs = self._get_args_from_dialog("CmdFIFO.DebugDelay", "DelayTime_s")
        if args is not None:
            self._invoke_rpc('CmdFIFO.DebugDelay', args, kwargs)

    def _get_args_from_dialog(self, func_name, args_in):
        args_okay = True
        args = ()
        kwargs = {}
        text, ok = QInputDialog.getText(
            self, func_name, "The selected RPC function requires arguments of the form:"
            f"\n\n{args_in}\n\n"
            "Please enter the arguments below as if you were calling\n"
            "the function in a Python shell (without outside parentheses).")
        if not ok:
            args_okay = False
        else:
            # make a tuple out of what gets entered...
            dlg_value = text
            try:
                # This is required for test_client to pass anything than
                # integers or strings
                def my_wrapper(*args, **kwargs):
                    return args, kwargs

                command_to_eval = "my_wrapper(" + dlg_value + ")"
                args, kwargs = eval(command_to_eval)
            except Exception as e:  # noqa
                # exception can happen during the eval statement
                if __debug__: print(e)  # noqa
                args_okay = False

                dlg = QMessageBox()
                dlg.setText('There was a problem with the typed arguments.\n\n'
                            f'Expected form: {args_in}\n'
                            f'What you typed: {dlg_value}\n\n'
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
        if not args_okay:
            args = None
        return args, kwargs

    def callback_test(self, returned_vars, fault):
        self.log_text_box.append(f"  *** Callback received.  Ret = {returned_vars}  Fault = {fault}\n")

    def on_rpc_button_click(self):
        if not isinstance(self.server, CmdFIFO.CmdFIFOServerProxy):
            raise ValueError(f"self.server has to be CmdFIFO.CmdFIFOServerProxy, got {type(self.server)} instead.")

        # figure out what to call...
        sender = self.sender()
        func_name = sender.method_name
        # set function method to what is in the choice box
        choice_str = self.cmd_type_drop_list.currentText()
        func_method = CmdTypeChoicesDict[choice_str]
        if func_method == CmdFIFO.CMD_TYPE_Callback:
            self.server.SetFunctionMode(func_name, func_method, self.callback_test)
        else:
            self.server.SetFunctionMode(func_name, func_method)
        # if args exist, prompt for this...
        args = self.rpc_method_dict[func_name]
        if args == '()':
            args = ()
            kwargs = {}
        else:
            # need to ask user for the arg_tuple to invoke the function...
            args, kwargs = self._get_args_from_dialog(func_name, args)
        if args is not None:
            self._invoke_rpc(func_name, args, kwargs)

    def create_rpc_buttons(self, rpc_method_dict):
        """
            Dynamically creates buttons in 'registered rpc' window.
        """
        if not isinstance(rpc_method_dict, dict):
            raise ValueError(f"rpc_method_dict has to be dict, got {type(rpc_method_dict)} instead.")

        self.rpc_method_dict = rpc_method_dict
        i = 0
        methods = list(rpc_method_dict.keys())
        methods.sort()
        self.rpc_buttons = []
        for method_name in methods:
            if (method_name.find("system.") < 0) and (method_name.find("CmdFIFO.") < 0):
                i += 1
                btn = QPushButton(f"  {method_name}")
                btn.clicked.connect(self.on_rpc_button_click)
                btn.method_name = method_name
                self.registered_rpcs_layout.addWidget(btn)
                self.rpc_buttons.append(btn)
                tool_tip = self.server.system.methodHelp(method_name)
                btn.setToolTip(tool_tip)


def main():
    try:
        options, _ = getopt.getopt(sys.argv[1:], 'a:p:c:hs', ['serveraddr=', 'serverport=', 'callbackaddr=', 'help', '--simple'])
    except getopt.GetoptError as e:
        if __debug__: print(e)  # noqa
        sys.exit(1)

    proxy_address = "127.0.0.1"
    proxy_port = 8001
    callback_server_address = 8002  # default
    simple_mode = False
    for o, a in options:
        if o in ['-h', '--help']:
            PrintUsage()
            sys.exit()
        if o in ['-a', '--serveraddr']:
            proxy_address = a
        if o in ['-p', '--serverport']:
            proxy_port = a
        if o in ['-c', '--callbackaddr']:
            callback_server_address = int(a)
        if o in ['-s', '--simple']:
            simple_mode = True

    #########
    # Set up the server proxy...
    server_url = f"http://{proxy_address}:{proxy_port}"
    if __debug__: print("***************")  # noqa
    if __debug__: print(f"Configuring connection to server at '{server_url}'")  # noqa
    if __debug__: print("***************")  # noqa
    try:
        server = CmdFIFO.CmdFIFOServerProxy(uri=server_url,
                                            IsDontCareConnection=False,
                                            ClientName="TestClient",
                                            CallbackURI="http://localhost:" + str(callback_server_address))
        # grab a list of the supported methods...
        if not simple_mode:
            rpc_method_list = server.system.listMethods()
            # Now build up a dictionary with the keys as method names and values as strings
            # describing the args...
            rpc_dict = {}
            for method in rpc_method_list:
                sig = str(server.system.methodSignature(method))
                # strip the self arg if a method...
                sig = sig.replace("(self,", "(", 1)
                sig = sig.replace("(self)", "()", 1)
                rpc_dict.setdefault(method, sig)
            if len(rpc_dict) == 0:
                sys.exit()

    except Exception as e:
        if __debug__: print("Trapped an exception when connecting to server:", e)  # noqa

    else:
        app = QApplication([])

        window = TestClientWidget()
        window.server = server

        window.dynamic_server_name_label.setText(server.CmdFIFO.GetName())
        window.dynamic_proxy_address_label.setText(proxy_address)
        window.dynamic_proxy_port_label.setText(str(proxy_port))

        callback_server = CmdFIFO.CmdFIFOSimpleCallbackServer(("localhost", callback_server_address),
                                                              CallbackList=(window.callback_test, ))
        callback_server.Launch()

        if not simple_mode:
            # Now autogenerate some buttons...
            window.create_rpc_buttons(rpc_dict)

        window.resize(960, 720)
        window.show()
        app.exec_()


if __name__ == "__main__":
    main()
