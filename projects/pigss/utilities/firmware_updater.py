import sys
import time
import psutil
import subprocess

from qtpy import QtCore
from qtpy.QtGui import QTextCursor
from qtpy.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout, QLabel,
                            QPushButton, QTextEdit, QVBoxLayout, QWidget,
                            QTableWidget, QTableWidgetItem, QFileDialog)


from back_end.madmapper.usb.serialmapper import SerialMapper
from back_end.piglet.piglet_driver import PigletBareDriver


def check_for_piggs_core_status():
    process_names = [p.info for p in psutil.process_iter(['name'])]
    triggers = ["pigss", "piglet"]
    software_running_found = False
    for process_name in process_names:
        for trigger in triggers:
            if trigger in process_name["name"].lower():
                software_running_found = True
                print(f"process '{process_name['name']}' is running")
                break
    return software_running_found


def check_for_valid_fw_file(file_path):
    # TODO
    return True


class PigletWidget(QWidget):
    device_counter = 0

    def __init__(self, device_configs, parent=None):
        super(PigletWidget, self).__init__(parent)
        self.device_configs = device_configs
        self.mgl = QVBoxLayout()
        self.setLayout(self.mgl)
        self.TEST_LABEL = QLabel("")
        self.device_number = PigletWidget.device_counter
        self.fw_file_path = None
        self.interface_to_be_locked = []
        PigletWidget.device_counter += 1

        self.mgl.addWidget(self.TEST_LABEL)

        if device_configs is not None:
            self.define(device_configs)

    def define(self, device_configs):
        self.device_configs = device_configs
        self.TEST_LABEL.setText(f"Device #{self.device_number}")
        self.mgl.addWidget(self.make_table())
        self.mgl.addWidget(self.make_bank_id_frame())
        self.mgl.addWidget(self.make_fw_update_frame())
        self.mgl.addWidget(self.make_log_box())

    def make_table(self):
        self.tableWidget = QTableWidget()

        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)

        row_count = 0
        for data_key in self.device_configs:
            if data_key not in ["Bank_ID", "Driver", "Baudrate", "RPC_Port"]:
                self.tableWidget.insertRow(row_count)
                self.tableWidget.setItem(row_count, 0, QTableWidgetItem(data_key))
                self.tableWidget.setItem(row_count, 1, QTableWidgetItem(self.device_configs[data_key]))
                row_count += 1

        self.tableWidget.setMinimumSize(QtCore.QSize(150, row_count*30+21))
        return self.tableWidget

    def make_bank_id_frame(self):
        self.bank_id_frame = QFrame()
        self.bank_id_layout = QHBoxLayout()
        self.bank_id_frame.setLayout(self.bank_id_layout)

        self.bank_id_label = QLabel("Bank_ID")
        self.bank_id_layout.addWidget(self.bank_id_label)

        self.bank_id_cb = QComboBox()
        self.bank_id_cb.addItems([str(i) for i in range(10)])
        self.bank_id_cb.setCurrentText(str(self.device_configs["Bank_ID"]))
        self.bank_id_cb.currentIndexChanged.connect(self.bank_id_selection_changed)
        self.bank_id_layout.addWidget(self.bank_id_cb)
        self.interface_to_be_locked.append(self.bank_id_cb)

        self.btn_bank_id_flush = QPushButton("Flush")
        self.btn_bank_id_flush.setEnabled(False)
        self.btn_bank_id_flush.clicked.connect(self.on_btn_bank_id_flush_click)
        self.bank_id_layout.addWidget(self.btn_bank_id_flush)
        self.interface_to_be_locked.append(self.btn_bank_id_flush)

        return self.bank_id_frame

    def bank_id_selection_changed(self):
        if self.bank_id_cb.currentText() != str(self.device_configs["Bank_ID"]):
            self.btn_bank_id_flush.setEnabled(True)
        else:
            self.btn_bank_id_flush.setEnabled(False)

    def on_btn_bank_id_flush_click(self):
        self.FlushBankIDThread = FlushBankIDThread(self, self.device_configs, str(self.bank_id_cb.currentText()))
        self.FlushBankIDThread.log_text_box_signal.connect(lambda p: self.log_fw_update((p)))
        self.FlushBankIDThread.start()

    def make_fw_update_frame(self):
        self.fw_update_frame = QFrame()
        self.fw_update_layout = QVBoxLayout()
        self.fw_update_frame.setLayout(self.fw_update_layout)

        self.fw_update_label = QLabel("Choose firmware file")
        self.fw_update_layout.addWidget(self.fw_update_label)

        self.fw_update_controls_frame = QFrame()
        self.fw_update_controls_layout = QHBoxLayout()
        self.fw_update_controls_frame.setLayout(self.fw_update_controls_layout)
        self.fw_update_layout.addWidget(self.fw_update_controls_frame)

        self.btn_open_file = QPushButton("Open file...")
        self.btn_open_file.clicked.connect(self.on_btn_open_file_click)
        self.fw_update_controls_layout.addWidget(self.btn_open_file)
        self.interface_to_be_locked.append(self.btn_open_file)

        self.btn_fw_flush = QPushButton("Flush Firmware")
        self.btn_fw_flush.setEnabled(False)
        self.btn_fw_flush.clicked.connect(self.on_btn_fw_flush_click)
        self.fw_update_controls_layout.addWidget(self.btn_fw_flush)
        self.interface_to_be_locked.append(self.btn_fw_flush)
        return self.fw_update_frame

    def make_log_box(self):

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setLineWrapMode(QTextEdit.NoWrap)
        self.log_box.moveCursor(QTextCursor.End)

        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

        return self.log_box

    def log_fw_update(self, text):
        if not text.endswith("\n"):
            text += "\n"
        self.log_box.insertPlainText(text)
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_btn_fw_flush_click(self):
        self.FlushTheFirmwareThread = FlushTheFirmwareThread(self, self.device_configs, self.fw_file_path)
        self.FlushTheFirmwareThread.log_text_box_signal.connect(lambda p: self.log_fw_update((p)))
        self.FlushTheFirmwareThread.start()

    def on_btn_open_file_click(self):
        file_path = QFileDialog.getOpenFileName(self, 'Open file', '/home/picarro/', "*.hex")[0]
        self.log_fw_update(f"File {file_path} picked\n")

        if check_for_valid_fw_file(file_path):
            self.fw_file_path = file_path
            self.btn_fw_flush.setEnabled(True)
        else:
            self.btn_fw_flush.setEnabled(False)
            self.log_fw_update(f"Not a valid firmware file\n")

    def lock_all_interface(self):
        self.preserved_interface_status = []
        for element in self.interface_to_be_locked:
            self.preserved_interface_status.append([element, element.isEnabled()])
            element.setEnabled(False)

    def unlock_all_interface(self):
        for element in self.preserved_interface_status:
            if element[1]:
                element[0].setEnabled(True)


class FirmwareUpdateWidget(QWidget):
    def __init__(self, parent=None):
        super(FirmwareUpdateWidget, self).__init__(parent)
        self.piggles_widgets = []
        self.mgl = QVBoxLayout()

        self.initGUI()
        self.setLayout(self.mgl)
        self.pigss_core_is_active = None

        self.set_GUI_to_pigss_core_status()
        self.CheckingForPiggsCoreThread = CheckingForPiggsCoreThread(self)
        self.CheckingForPiggsCoreThread.lock_interface_signal.connect(self.set_GUI_to_pigss_core_status)

        self.CheckingForPiggsCoreThread.start()
        self.found_hardware = None

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

        self.found_hardware_layout = QHBoxLayout()
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
            for piglet_widget in self.piggles_widgets:
                piglet_widget.lock_all_interface()
        else:
            self.dynamic_piggs_core_status_label.setText("NOT ACTIVE")
            self.dynamic_piggs_core_status_label.setStyleSheet('color: green')
            self.btn_scan_for_hardware.setEnabled(True)
            self.prescan_message_label.setText("You can scan for harfware now")
            for piglet_widget in self.piggles_widgets:
                piglet_widget.unlock_all_interface()

    def create_gui_for_found_hardware(self, found_hardware):
        self.remove_gui_widgets()
        self.found_hardware = found_hardware
        for device_path in self.found_hardware:
            if self.found_hardware[device_path]["Driver"] == "PigletDriver":
                piggles_widget = PigletWidget(self.found_hardware[device_path], self)
                self.found_hardware_layout.addWidget(piggles_widget)
                self.piggles_widgets.append(piggles_widget)

    def remove_gui_widgets(self):
        for piggles_widget in self.piggles_widgets:
            self.found_hardware_layout.removeWidget(piggles_widget)

    def on_scan_click(self):
        self.ScanHardwareThread = ScanHardwareThread(self)
        self.ScanHardwareThread.serial_devices_signal.connect(lambda p: self.create_gui_for_found_hardware(p))
        self.ScanHardwareThread.start()


class CheckingForPiggsCoreThread(QtCore.QThread):
    lock_interface_signal = QtCore.Signal()

    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent

    def run(self):
        while True:
            new_status = check_for_piggs_core_status()

            if new_status != self.parent.pigss_core_is_active:
                self.parent.pigss_core_is_active = new_status
                self.lock_interface_signal.emit()
            time.sleep(1)


class ScanHardwareThread(QtCore.QThread):
    serial_devices_signal = QtCore.Signal(object)

    def __init__(self, parent):
        QtCore.QThread.__init__(self)
        self.parent = parent

    def run(self):
        self.parent.btn_scan_for_hardware.setEnabled(False)
        self.parent.btn_scan_for_hardware.setText("Scanning...")

        self.serialmapper = SerialMapper()
        serial_devices = self.serialmapper.get_usb_serial_devices()["Serial_Devices"]

        self.parent.btn_scan_for_hardware.setText("Scan")
        self.serial_devices_signal.emit(serial_devices)
        self.parent.btn_scan_for_hardware.setEnabled(True)


class FlushTheFirmwareThread(QtCore.QThread):
    log_text_box_signal = QtCore.Signal(str)

    def __init__(self, parent, device_configs, file_path):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.device_configs = device_configs
        self.file_path = file_path

    def run(self):
        self.parent.btn_fw_flush.setEnabled(False)
        self.parent.btn_fw_flush.setText("Flushing...")
        self.log_text_box_signal.emit("Flushing...\n")

        cmd = "avrdude -v -p m2560 -P $(VCP) -c arduino -b $(avrdude_baud) -F -u -U flash:w:$(hex_file)"
        cmd = cmd.replace("$(VCP)", self.device_configs["Path"])
        cmd = cmd.replace("$(avrdude_baud)", "230400")
        cmd = cmd.replace("$(hex_file)", self.file_path)
        subprocess.call(cmd.split())

        self.parent.btn_fw_flush.setText("Flush")

        self.log_text_box_signal.emit("Done\n")
        self.parent.btn_fw_flush.setEnabled(False)


class FlushBankIDThread(QtCore.QThread):
    log_text_box_signal = QtCore.Signal(str)

    def __init__(self, parent, device_configs, new_bank_id):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.device_configs = device_configs
        self.new_bank_id = new_bank_id

    def run(self):
        self.parent.btn_bank_id_flush.setEnabled(False)
        self.parent.btn_bank_id_flush.setText("Flushing...")
        self.log_text_box_signal.emit(f"Flushing new Bank_ID to be {self.new_bank_id}\n")

        self.piglet_driver = PigletBareDriver(port=self.device_configs["Path"], baudrate=230400)
        self.piglet_driver.logger.verbose = True
        self.piglet_driver.set_slot_id(int(self.new_bank_id))
        self.piglet_driver.close()

        self.parent.device_configs["Bank_ID"] = self.new_bank_id
        self.parent.btn_bank_id_flush.setText("Flush")
        self.log_text_box_signal.emit("Done\n")
        self.parent.btn_bank_id_flush.setEnabled(False)


def main():
    app = QApplication([])

    window = FirmwareUpdateWidget()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()

    """TODO
    check for valid firmware file
    """
