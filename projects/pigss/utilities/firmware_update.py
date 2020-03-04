import time


from qtpy import QtCore
from qtpy.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton,
                            QScrollArea, QTextEdit, QVBoxLayout, QWidget)


from back_end.madmapper.usb.serialmapper import SerialMapper

def check_for_piggs_core_status():
    # return False
    # time.sleep(1)
    return time.time()%10>5

# class PigletWidget(QWidget):


class FirmwareUpdateWidget(QWidget):
    def __init__(self, parent=None):
        super(FirmwareUpdateWidget, self).__init__(parent)
        self.mgl = QVBoxLayout()
        self.initGUI()
        self.setLayout(self.mgl)
        self.pigss_core_is_active = None

        self.set_GUI_to_pigss_core_status()
        self.CheckingForPiggsCoreThread = CheckingForPiggsCoreThread(self)
        self.CheckingForPiggsCoreThread.start()

        return

    def initGUI(self):
        # Initiate all GUI
        self.piggs_core_status_label = QLabel("Pigss-core Status: ")
        self.dynamic_piggs_core_status_label = QLabel("---")
        self.piggs_core_status_layout = QHBoxLayout()
        self.piggs_core_status_frame = QFrame()

        self.piggs_core_status_layout.addWidget(self.piggs_core_status_label)
        self.piggs_core_status_layout.addWidget(self.dynamic_piggs_core_status_label)

        self.piggs_core_status_frame.setLayout(self.piggs_core_status_layout)

        self.mgl.addWidget(self.piggs_core_status_frame)


        self.prescan_message_label = QLabel("You --- scan for harfware now")
        self.btn_scan_for_hardware = QPushButton("Scan")



        self.btn_scan_for_hardware.clicked.connect(self.on_scan_click)

        self.scan_hardware_layout = QHBoxLayout()
        self.scan_hardware_frame = QFrame()

        self.scan_hardware_layout.addWidget(self.prescan_message_label)
        self.scan_hardware_layout.addWidget(self.btn_scan_for_hardware)

        self.scan_hardware_frame.setLayout(self.scan_hardware_layout)

        self.mgl.addWidget(self.scan_hardware_frame)




        self.found_hardware_layout = QVBoxLayout()
        self.found_hardware_frame = QFrame()

        self.found_hardware_frame.setLayout(self.found_hardware_layout)

        self.mgl.addWidget(self.found_hardware_frame)




    def set_GUI_to_pigss_core_status(self):
        if self.pigss_core_is_active is None:
            self.dynamic_piggs_core_status_label.setText("Pending")
            self.btn_scan_for_hardware.setEnabled(False)
            self.prescan_message_label.setText("You can't scan for harfware now")

        elif self.pigss_core_is_active:
            self.dynamic_piggs_core_status_label.setText("ACTIVE")
            self.dynamic_piggs_core_status_label.setStyleSheet('color: red')
            self.btn_scan_for_hardware.setEnabled(False)
            self.prescan_message_label.setText("You can't scan for harfware now")
        else:
            self.dynamic_piggs_core_status_label.setText("NOT ACTIVE")
            self.dynamic_piggs_core_status_label.setStyleSheet('color: green')
            self.btn_scan_for_hardware.setEnabled(True)
            self.prescan_message_label.setText("You can scan for harfware now")



    def on_scan_click(self):
        # print("scanning")
        self.btn_scan_for_hardware.setText("Scanning...")
        self.ScanHardware = ScanHardware(self)
        self.ScanHardware.start()


class CheckingForPiggsCoreThread(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent 

        
    def run(self):
        while True:
            new_status = check_for_piggs_core_status()

            if new_status != self.parent.pigss_core_is_active:
                self.parent.pigss_core_is_active = new_status
                self.parent.set_GUI_to_pigss_core_status()
            time.sleep(1)


class ScanHardware(QtCore.QThread):
    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent
        
    def run(self):
        self.serialmapper = SerialMapper()
        serial_devices = self.serialmapper.get_usb_serial_devices()
        print(serial_devices)
        self.btn_scan_for_hardware.setText("Scan")


        # self.__init_items()
        # self.__init_layouts()
        # self.__set_layouts()
        # self.__add_widgets()
        # self.__init_core_rpc_buttons()
        # self.__init_server_labels()
        # self.__set_properties()
        # return self.mgl

    # def __init_items(self):
    #     # initiate all the items: qboxes, qtext, qframe
    #     self.cmd_type_drop_list = QComboBox()
    #     self.log_text_box = QTextEdit()
    #     self.left_column_interface = QGroupBox()
    #     self.right_column_interface = QGroupBox()
    #     self.registered_rpcs_widget = QGroupBox("Registered RPCs")
    #     self.registered_rpcs = QFrame()
    #     self.registered_rpcs_widget_scrollable = QScrollArea()
    #     self.cmd_fifo_rpc_widget = QGroupBox("CmdFIFO RPCs")
    #     self.server_information_widget = QGroupBox("Server Information")
    #     self.transactions_widget = QGroupBox("Transactions")

    # def __init_layouts(self):
    #     # initiate all the layouts
    #     self.left_column_interface_layout = QVBoxLayout()
    #     self.right_column_interface_layout = QVBoxLayout()
    #     self.registered_rpcs_widget_layout = QVBoxLayout()
    #     self.registered_rpcs_layout = QVBoxLayout()
    #     self.cmd_fifo_rpc_widget_layout = QVBoxLayout()
    #     self.server_information_widget_layout = QHBoxLayout()
    #     self.transactions_widget_layout = QHBoxLayout()

    # def __set_layouts(self):
    #     # apply all the layouts to corresponded boxes
    #     self.registered_rpcs_widget.setLayout(self.registered_rpcs_widget_layout)
    #     self.registered_rpcs.setLayout(self.registered_rpcs_layout)
    #     self.cmd_fifo_rpc_widget.setLayout(self.cmd_fifo_rpc_widget_layout)
    #     self.server_information_widget.setLayout(self.server_information_widget_layout)
    #     self.transactions_widget.setLayout(self.transactions_widget_layout)
    #     self.left_column_interface.setLayout(self.left_column_interface_layout)
    #     self.right_column_interface.setLayout(self.right_column_interface_layout)
    #     self.registered_rpcs_widget_scrollable.setWidget(self.registered_rpcs)

    # def __add_widgets(self):
    #     # add all the widgets to the layouts
    #     self.mgl.addWidget(self.left_column_interface)
    #     self.mgl.addWidget(self.right_column_interface)
    #     self.transactions_widget_layout.addWidget(self.log_text_box)
    #     self.registered_rpcs_widget_layout.addWidget(self.cmd_type_drop_list)
    #     self.registered_rpcs_widget_layout.addWidget(self.registered_rpcs_widget_scrollable)

    #     self.left_column_interface_layout.addWidget(self.registered_rpcs_widget)
    #     self.left_column_interface_layout.addWidget(self.cmd_fifo_rpc_widget)
    #     self.right_column_interface_layout.addWidget(self.server_information_widget)
    #     self.right_column_interface_layout.addWidget(self.transactions_widget)

    # def __set_properties(self):
    #     # set some properties
    #     self.setWindowTitle("CmdFIFO Test Client")
    #     choice_list = list(CmdTypeChoicesDict.keys())
    #     choice_list.sort()
    #     self.cmd_type_drop_list.addItems(choice_list)
    #     self.cmd_type_drop_list.setCurrentIndex(2)
    #     self.left_column_interface.setFixedWidth(250)
    #     self.registered_rpcs_widget_scrollable.setWidgetResizable(True)
    #     self.log_text_box.setReadOnly(True)

    #     self.server_information_widget_layout.setAlignment(QtCore.Qt.AlignLeft)
    #     self.registered_rpcs_layout.setAlignment(QtCore.Qt.AlignTop)

    # def __init_core_rpc_buttons(self):
    #     # init the buttons that will call core CmdFIFO RPCs...
    #     self.btn_get_name = QPushButton("Get Server Name")
    #     self.btn_get_description = QPushButton("Get Server Desc")
    #     self.btn_get_version = QPushButton("Get Server Version")
    #     self.btn_get_queue_length = QPushButton("Get Queue Length")
    #     self.btn_enable_logging = QPushButton("Enable Logging")
    #     self.btn_.setEnabled(False)_logging = QPushButton(".setEnabled(False) Logging")
    #     self.btn_ping_fifo = QPushButton("Ping FIFO")
    #     self.btn_ping_dispatcher = QPushButton("Ping Dispatcher")
    #     self.btn_show_fifo_gui = QPushButton("Show FIFO GUI")
    #     self.btn_hide_fifo_gui = QPushButton("Hide FIFO GUI")
    #     self.btn_get_process_id = QPushButton("Get Process ID")
    #     self.btn_stop_server = QPushButton("Stop Server")
    #     self.btn_kill_server = QPushButton("Kill Server")
    #     self.btn_debug_delay = QPushButton("Debug Delay")

    #     # bind buttons to functions
    #     self.btn_get_name.clicked.connect(self.on_get_name_click)
    #     self.btn_get_description.clicked.connect(self.on_get_description_click)
    #     self.btn_get_version.clicked.connect(self.on_get_version_click)
    #     self.btn_get_queue_length.clicked.connect(self.on_get_queue_length_click)
    #     self.btn_show_fifo_gui.clicked.connect(self.on_show_fifo_gui_click)
    #     self.btn_hide_fifo_gui.clicked.connect(self.on_hide_fifo_gui_click)
    #     self.btn_enable_logging.clicked.connect(self.on_enable_logging_click)
    #     self.btn_.setEnabled(False)_logging.clicked.connect(self.on_.setEnabled(False)_logging_click)
    #     self.btn_get_process_id.clicked.connect(self.on_get_process_id_click)
    #     self.btn_stop_server.clicked.connect(self.on_stop_server_click)
    #     self.btn_kill_server.clicked.connect(self.on_kill_server_click)
    #     self.btn_ping_fifo.clicked.connect(self.on_ping_fifo_click)
    #     self.btn_ping_dispatcher.clicked.connect(self.on_ping_dispatcher_click)
    #     self.btn_debug_delay.clicked.connect(self.on_debug_delay_click)

    #     # add buttons to the cmd_fifo_rpc_widget_layout
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_name)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_description)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_version)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_queue_length)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_enable_logging)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_.setEnabled(False)_logging)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_ping_fifo)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_ping_dispatcher)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_show_fifo_gui)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_hide_fifo_gui)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_get_process_id)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_stop_server)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_kill_server)
    #     self.cmd_fifo_rpc_widget_layout.addWidget(self.btn_debug_delay)

    # def __init_server_labels(self):
    #     self.server_name_label = QLabel("Name:")
    #     self.dynamic_server_name_label = QLabel("---")
    #     self.proxy_address_label = QLabel("Address:")
    #     self.dynamic_proxy_address_label = QLabel("---")
    #     self.proxy_port_label = QLabel("Port:")
    #     self.dynamic_proxy_port_label = QLabel("---")

    #     self.server_information_widget_layout.addWidget(self.server_name_label)
    #     self.server_information_widget_layout.addWidget(self.dynamic_server_name_label)
    #     self.server_information_widget_layout.addWidget(self.proxy_address_label)
    #     self.server_information_widget_layout.addWidget(self.dynamic_proxy_address_label)
    #     self.server_information_widget_layout.addWidget(self.proxy_port_label)
    #     self.server_information_widget_layout.addWidget(self.dynamic_proxy_port_label)


def main():
    app = QApplication([])

    window = FirmwareUpdateWidget()
    # window.resize(960, 720)
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()