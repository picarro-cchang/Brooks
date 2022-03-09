#!/usr/bin/python

import sys
import os
import threading
import time
import getopt
import shutil
import traceback
import subprocess
import signal
from datetime import datetime as dt
from PyQt4 import QtGui, QtCore
from configobj import ConfigObj

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_DRIVER, RPC_PORT_FREQ_CONVERTER, RPC_PORT_SAMPLE_MGR

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_DRIVER, "IntegrationTool")
SampleManager = CmdFIFO.CmdFIFOServerProxy(
    "http://localhost:%d" % RPC_PORT_SAMPLE_MGR,
    "IntegrationTool",
    IsDontCareConnection=False
)


if hasattr(sys, "frozen"):  #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
AppPath = os.path.abspath(AppPath)

DEFAULT_CONFIG_NAME = "field_laser_cal.ini"

class InterfaceFetcher(object):
    def __init__(self):
        self.memo = {}

    def __getattr__(self, item):
        if item not in self.memo:
            value = Driver.interfaceValue(item)
            if value != 'undefined':
                self.memo[item] = value
            else:
                raise LookupError("Cannot fetch %s in interface. Is Driver running?" % item)
        return self.memo[item]


class Window(QtGui.QMainWindow):
    msg_signal = QtCore.pyqtSignal(str)
    progress_signal = QtCore.pyqtSignal(float)
    def __init__(self, config_file):
        super(Window, self).__init__()
        self.setWindowTitle('Field Laser Cal Launcher')
        self.setMinimumSize(500, 300)
        central_widget = QtGui.QWidget()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.message_box = QtGui.QTextEdit()
        self.progress_bar = QtGui.QProgressBar()
        self.nn_button = QtGui.QPushButton('NN Laser')
        self.nn_button.clicked.connect(self.run_nn_laser_cal)
        self.uu_button = QtGui.QPushButton('UU Laser')
        self.uu_button.clicked.connect(self.run_uu_laser_cal)
        self.msg_signal.connect(self.add_msg)
        self.progress_signal.connect(self.set_progress)
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.nn_button)
        hbox.addWidget(self.uu_button)
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.message_box)
        vbox.addLayout(hbox)
        central_widget.setLayout(vbox)
        self.msg_signal.emit('Select Laser to Calibrate')
        self.setCentralWidget(central_widget)
        self.show()
        self.cp = CustomConfigObj(config_file)
        self.CAL_DIR = self.cp.get("Main", "INSTR_CAL_DIR")
        self.INTEGRATION_DIR = self.cp.get("Main", "INTEGRATION_DIR")
        self.UTILS_DIR = self.cp.get("Main", "UTILS_DIR")
        self.HOST_DIR = self.cp.get("Main", "HOST_DIR")
        self.supervisor = self.cp.get("Main", "SUPERVISOR")
        self.mode = self.cp.get("Main", "MODE")

    @property
    def current_time(self):
        return dt.now().strftime("%d/%m/%Y %H:%M:%S")

    def add_msg(self, msg):
        msg = ''.join([self.current_time, ': ', str(msg)])
        self.message_box.append(msg)

    def set_progress(self, percent):
        self.progress_bar.setValue(percent)

    def disable_buttons(self):
        self.uu_button.setEnabled(False)
        self.nn_button.setEnabled(False)

    def run_nn_laser_cal(self):
        """Run the NN laser cal"""
        self.SGDBR_CAL = self.cp["FieldLaserCalibration"]["NN"]["SGDBR_CAL_FIELD"]
        self.msg_signal.emit('Preparing laser cal for UU laser')
        self.disable_buttons()
        pressure_mode = self.cp.get('Main', 'PRESSUREMODE')
        self.setPressureMode(pressure_mode)
        newThread = threading.Thread(target=self._startLcalMode)
        newThread.setDaemon(True)
        newThread.start()

    def run_uu_laser_cal(self):
        """Run the UU laser cal"""
        self.SGDBR_CAL = self.cp["FieldLaserCalibration"]["NN"]["SGDBR_CAL_FIELD"]
        self.msg_signal.emit('Preparing laser cal for NN laser')
        self.disable_buttons()
        pressure_mode = self.cp.get('Main', 'PRESSUREMODE')
        self.setPressureMode(pressure_mode)
        newThread = threading.Thread(target=self._startLcalMode)
        newThread.setDaemon(True)
        newThread.start()

    def setPressureMode(self, pressureModeToSet):
        """
        This will set all the parameters and files used for different pressure modes.
        Currently we are not doing anything but 140, but this will be needed when
        we operate at different pressures
        """
        self.add_msg(' '.join(['Getting configuration for', pressureModeToSet]))
        CAL_DIR = self.CAL_DIR
        PS = "PressureSwitcher"
        ini_keys = ["warmbox_cal", "warmbox_cal_active", "hotbox_cal",
        "hotbox_cal_active", "master_sgdbr", "integration_dir"]
        file_dict = {}

        pressure_keys = self.cp[PS].keys()
        if pressureModeToSet not in pressure_keys:
            raise ValueError("Pressure {} not present in Ini for Integration Tool calibration".format(pressureModeToSet))

        if pressureModeToSet == "450_Torr":
            self.pressureMode = "450 Torr"
        else:
            self.pressureMode = "140_Torr"

        for key in ini_keys:
            file_dict[key] = self.cp[PS][pressureModeToSet][key.upper()]

        self.wbCalFile = os.path.join(CAL_DIR, file_dict["warmbox_cal"] + ".ini")
        self.wbCalBackup = os.path.join(CAL_DIR, (file_dict["warmbox_cal"]+"_Backup") + ".ini")
        self.wbCalDuplicate = os.path.join(file_dict["integration_dir"], file_dict["warmbox_cal"] + ".ini")
        self.wbCalActive = os.path.join(CAL_DIR, file_dict["warmbox_cal_active"] + "ini")
        self.hbCalFile = os.path.join(CAL_DIR, file_dict["hotbox_cal"] + "ini")
        self.hbCalActive = os.path.join(CAL_DIR, file_dict["hotbox_cal_active"] + "ini")
        self.INTEGRATION_DIR = file_dict["integration_dir"]
        self.master_sgdbr = file_dict["master_sgdbr"]

    def _onFieldLaserCal1(self):
        """
        Here we copy the warm box file so that we can set the temperatures/pressures correctly
        """
        coSGDBR = ConfigObj(os.path.join(self.CAL_DIR, self.SGDBR_CAL), raise_errors=True)
        statusDict = Driver.getWarmingState()

        if 'base_name' in coSGDBR['Paths']:
            print('base name')
            strLaserTemp = coSGDBR['Parameters']['Tlaser']
            fltLaserTemp = float(strLaserTemp)
            intLaserTemp = int(fltLaserTemp)
            strLaserTemp = str(intLaserTemp)
            newDir = time.strftime(self.INTEGRATION_DIR + "/LaserCal_" + strLaserTemp + "_" + self.SGDBR_CAL + "/%Y%m%d_%H%M%S")

            print(newDir)
            coSGDBR['Paths']['base_name']=newDir
            print(self.master_sgdbr)

            coSGDBR.write()
        # Make copy of warmboxcal to integration directory
        try:
            print('shutil')
            shutil.copy2(self.wbCalFile, self.wbCalDuplicate)
            self.msg_signal.emit("Copying %s to %s..." % (self.wbCalFile, self.wbCalDuplicate))
        except Exception, err:
            self.msg_signal.emit("%s" % err)

        time.sleep(2)
        self._onFieldLaserCal2()

    def _onFieldLaserCal2(self):
        """
        This method will start the driver, then start the sample manager. It will check that 
        pressures and temperatures are locked and within tolerance before launching the field laser cal
        """
        interface = InterfaceFetcher()
        cur_value = self.progress_bar.value()
        self.msg_signal.emit('Fetching Interface')
        for step in range(8):
            new_val = cur_value + step*4.0
            self.progress_signal.emit(new_val)
            time.sleep(2)
        timeStart = time.time()

        while True:
            try:
                self.msg_signal.emit('Driver Starting Engine')
                Driver.startEngine()
                SampleManager.FlowStart()
                break
            except Exception, err:
                print('Error = ', err)
                pass
            time.sleep(2)
            print('waiting for Driver / Sampler Manager to start ', (time.time() - timeStart))
            if (time.time() - timeStart) > 60:
                self.msg_signal.emit("Driver failed to start: Exiting Field Laser Cal")
                break

        Driver.startEngine()
        lock_ok = 0
        cur_value = self.progress_bar.value()
        self.msg_signal.emit('Checking Pressure and Temperature Stabilization')
        while True:
            lockStatus = Driver.getLockStatus()
            warmingState = Driver.getWarmingState()
            while Driver.rdDasReg("VALVE_CNTRL_STATE_REGISTER") == interface.VALVE_CNTRL_DisabledState:
                self.msg_signal.emit("\rWarm Box: %.2f C, Hot Box: %.2f C, Pressure: %.2f Torr" %
                         (warmingState["WarmBoxTemperature"][0], warmingState["CavityTemperature"][0], warmingState["CavityPressure"][0]))
                print('in sample manager',Driver.rdDasReg("VALVE_CNTRL_STATE_REGISTER"),interface.VALVE_CNTRL_DisabledState)
                try:
                    SampleManager.FlowStart()
                except:
                    pass
                if abs(warmingState["CavityTemperature"][0] - warmingState["CavityTemperature"][1]) > 2:
                    self.msg_signal.emit('Warming cavity:  this may take a while.  Next Update in 30 seconds')
                    time.sleep(30)
                time.sleep(2.0)
            time.sleep(3.0)
            if lockStatus["warmChamberTempLockStatus"] == "Locked" and lockStatus["cavityTempLockStatus"] == "Locked" and abs(
                warmingState["CavityPressure"][0] - warmingState["CavityPressure"][1]) < 0.5:
                lock_ok += 1
                msg = ' '.join(['Verifying Temp and Pressure Stable', str(lock_ok)])
                self.msg_signal.emit(msg)
            else:
                lock_ok = 0
                self.msg_signal.emit("\rPressure Stabilizing: Warm Box: %.2f C, Hot Box: %.2f C, Pressure: %.2f Torr" %
                         (warmingState["WarmBoxTemperature"][0], warmingState["CavityTemperature"][0], warmingState["CavityPressure"][0]))

            if lock_ok > 5:
                break

        self.msg_signal.emit('Temperatures and Pressure Locked.  Starting LaserCal')

        try:
            self.progress_signal.emit(100.0)
            path = os.path.join(self.CAL_DIR, self.SGDBR_CAL)
            cmd = ["sgdbr-calibration", "-c", path, "-s", "0"]# %s" % (os.path.join(self.CAL_DIR, self.SGDBR_CAL)) # -s 0
            #os.system(cmd)
            subprocess.Popen(cmd)            
            time.sleep(2.0)

            self.msg_signal.emit("Laser Cal started, quitting launcher.")
            time.sleep(1)
            self.close()
            
        except Exception, err:
            self.msg_signal.emit("Laser Cal failed: %s" % err)

        os.chdir(self.INTEGRATION_DIR)

    def _startLcalMode(self):
        """
        This is the first step of the process where we stop the current mode (currently no op),
        and start the laser cal mode.  Then we go into the warmbox copy nad pressure/temp stabilization
        """
        executable = self.cp["FieldLaserCalibration"]["EXE"]["Executable"]
        iniFile_path = os.path.join(self.UTILS_DIR, self.supervisor)
        start_cmd = ["python", executable, "-c", iniFile_path, "-m", self.mode, "-k"]
        try:
            self.msg_signal.emit("Stopping Current Mode.")
            for step in range(8):
                self.progress_signal.emit(step*4.0)
                time.sleep(2)
            self.msg_signal.emit("Starting Laser Cal Mode.")
            cur_value = self.progress_bar.value()
            for step in range(4):
                new_val = cur_value + step*4.0
                self.progress_signal.emit(new_val)
                time.sleep(2)
            subprocess.Popen(start_cmd)
            time.sleep(2)
            self._onFieldLaserCal1()
        except Exception, err:
            self.msg_signal.emit("Laser Cal Mode failed to start: %s" % err)
            self.msg_signal.emit(traceback.format_exc())

def handleCommandSwitches():
    shortOpts = "c:"
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

    #Start with option defaults...
    configFile = os.path.dirname(AppPath) + "/" + DEFAULT_CONFIG_NAME

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile

    return configFile

if __name__ == '__main__':
    config_file = handleCommandSwitches()
    app = QtGui.QApplication(sys.argv)
    gui = Window(config_file)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec_())