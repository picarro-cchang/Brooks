import os
import sys
import time
import getopt
import math
import random
import threading
import requests
import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

from Host.Common.CustomConfigObj import CustomConfigObj

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

validation_steps = {2:"zero_air", 4:"calibrant1", 6:"calibrant2", 8:"calibrant3"}

validation_procedure = [
    ("Introduction to System Validation", """
        <p>This validation procedure is based on sequentially introducing zero air and three methane standards.</p>
        <p><b>Procedure Duration</b>
            <ul>
                <li>20-60 minutes for data acquisition</li>
                <li>5-15 minutes for data analysis</li>
            </ul>
        </p>
        <p><b>Required Supplies</b>
            <ul>
                <li>Cylinder of zero air (dry synthetic hydrocarbon-free air.)</li>
                <li>Three methane standard cylinders containing 2, 10, and 100 ppm of methane certified at +/- 2% composition accuracy.</li>
                <li>One or more two-stage regulators. The second stage should be capable of accurately delivering 2-3 psi (0.1-0.2 bar) of line pressure. 
                Recommend using a 0-15 psi (0-1 bar) output range.</li>
                <li>Sufficient tubing to connect the regulator(s) to the instrument. </li>
                <li>1/4" Ultra Torr union (optional but highly recommended). </li>
            </ul>
        </p>
        <p><b>Safety</b><br>
        At the concentrations used here, methane poses zero health, reactivity, or flammability risks. 
        Follow all safety conventions appropriate for work with compressed gases, including use of eye protection, physical restraint of cylinders, etc.
        </p>
    """),
    ("Zero-Air Measurement: Preparation", """
        <ol>
            <li>Attach a regulator to the zero air source if not already installed, with the output pressure set to zero. 
            Open the cylinder valve and adjust the output line pressure upwards to 2-3 psi (0.1-0.2 bar). </li>
            <li>Attach the zero air line to the instrument.</li>
        </ol>
    """),
    ("Zero-Air Measurement", """
        <p><b>Data Collection</b></p>
        <p>It will take about two minutes for the cavity pressure to stabilize, and approximately five minutes for collecting data.</p>
    """),
    ("Calibrant 1: Preparation", """
        <p>Attach a methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </p>
        <p>Enter nominal concentration of methane gas below. </p>
    """),
    ("Calibrant 1 Measurement", """
        <p><b>Data Collection</b></p>
        <p>It will take about two minutes for the cavity pressure to stabilize, and approximately five minutes for collecting data.</p>
    """),
    ("Calibrant 2: Preparation", """
        <p>Attach the second methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </p>
        <p>Enter nominal concentration of methane gas below. </p>
    """),
    ("Calibrant 2 Measurement", """
        <p><b>Data Collection</b></p>
        <p>It will take about two minutes for the cavity pressure to stabilize, and approximately five minutes for collecting data.</p>
    """),
    ("Calibrant 3: Preparation", """
        <p>Attach the third methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </p>
        <p>Enter nominal concentration of methane gas below. </p>
    """),
    ("Calibrant 3 Measurement", """
        <p><b>Collecting data...</b></p>
        <p>It will take about two minutes for the cavity pressure to stabilize, and approximately five minutes for collecting data.</p>
    """)]
    
class TimeSeriesData(object):
    def __init__(self, max_size):
        self.xdata = np.zeros(max_size)
        self.ydata = np.zeros(max_size)
        self.max_size = max_size
        self.pointer = 0
        
    def put(self, x, y):
        if self.pointer == self.max_size:
            # move data on the second half of array to the first half
            low_limit = int(np.ceil(self.max_size / 2.0))
            self.pointer = self.max_size - low_limit
            self.xdata[:self.pointer] = self.xdata[low_limit:]
            self.ydata[:self.pointer] = self.ydata[low_limit:]
        self.xdata[self.pointer] = x
        self.ydata[self.pointer] = y
        self.pointer += 1
            
    def get(self):
        return (self.xdata[:self.pointer], self.ydata[:self.pointer])

class H2O2ValidationFrame(QMainWindow):
    def __init__(self, configFile, simulation, parent=None):
        if not os.path.exists(configFile):
            print "Config file not found: %s" % configFile
            sys.exit(0)
        self.config = CustomConfigObj(configFile)
        self.simulation = simulation
        self.load_config()
        super(H2O2ValidationFrame, self).__init__(parent)
        self.setWindowTitle("H2O2 Validation")
        #self.setWindowState(Qt.WindowFullScreen)
        self.style_data = ""
        with open('styleSheet.qss', 'r') as f:
            self.style_data = f.read()
        self.setStyleSheet(self.style_data)
        self.create_widgets()
        self.set_connections()
        self.resize(1200,800)        
        
        self.host_session = requests.Session()
        self.current_step = 0
        self.record_status = ""
        self.zero_air_step = validation_steps.keys()[validation_steps.values().index("zero_air")]
        self.validation_data = dict(H2O2=[], zero_air=[], calibrant1=[], calibrant2=[], calibrant3=[])
        self.validation_results = {}
        self.ch4_data = TimeSeriesData(100)
        
        if self.simulation:
            self.simulation_env = {func: getattr(math, func) for func in dir(math) if not func.startswith("__")}
            self.simulation_env.update({'random':  random.random, 'x': 0})
            
    def load_config(self):
        self.wait_time_before_collection = self.config.getint("Setup", "Wait_Time_before_Data_Collection")
        self.data_collection_time = self.config.getint("Setup", "Data_Collection_Time")
        self.report_dir = self.config.get("Setup", "Report_Directory")
        if self.simulation:
            self.simulation_dict = dict(
                H2O2=self.config.get("Simulation", "H2O2", "0.0"),
                CH4=self.config.get("Simulation", "CH4", "0.0"),
                CH4_zero_air=self.config.get("Simulation", "CH4_zero_air", "0.0"),
                CH4_calibrant1=self.config.get("Simulation", "CH4_calibrant1", None),
                CH4_calibrant2=self.config.get("Simulation", "CH4_calibrant2", None),
                CH4_calibrant3=self.config.get("Simulation", "CH4_calibrant3", None)
            )
            self.ch4_simulation = self.simulation_dict["CH4"]
            
    def run_simulation(self):
        index = 0
        while True:
            if self.current_step in validation_steps:
                step = "CH4_%s" % (validation_steps[self.current_step])
                if self.simulation_dict[step] is not None:
                    self.ch4_simulation = self.simulation_dict[step]
            ch4 = self.run_simulation_expression(self.ch4_simulation)
            h2o2 = self.run_simulation_expression(self.simulation_dict['H2O2'])
            self.process_data(index, ch4, h2o2)
            index += 1
            self.simulation_env['x'] += 1
            time.sleep(1)
            
    def process_data(self, xdata, ch4, h2o2):
        # save data
        if len(self.record_status) > 0:
            self.validation_data[self.record_status].append(ch4)
            if self.record_status == "zero_air": 
                self.validation_data["H2O2"].append(h2o2)
        # display data
        self.display_conc_ch4.setText("%.3f" % ch4)
        self.display_conc_h2o2.setText("%.3f" % h2o2)
        self.ch4_data.put(xdata, ch4)
        self.ch4_plot.setData(*self.ch4_data.get())            
            
    def run_simulation_expression(self, expression):
        if len(expression) > 0:
            exec "simulation_result=" + expression in self.simulation_env
            return self.simulation_env["simulation_result"]
        else:
            return 0.0
        
    def create_widgets(self):
        self.measurement_timer = QTimer()
        
        self.top_frame = QWidget()
        self.top_frame.setMaximumHeight(150)
        self.display_conc_ch4 = QLabel("0.00")
        self.display_conc_ch4.setAccessibleName("concentration")
        self.display_conc_ch4.setFrameShape(QFrame.Panel)
        self.display_conc_ch4.setFixedWidth(100)
        self.display_conc_h2o2 = QLabel("0.00")
        self.display_conc_h2o2.setAccessibleName("concentration")
        self.display_conc_h2o2.setFrameShape(QFrame.Panel)
        self.display_conc_h2o2.setFixedWidth(100)
        time_series_plot = pg.PlotWidget()
        time_series_plot.showGrid(x=True, y=True)
        time_series_plot.setLabels(left="CH4 (ppm)")
        self.ch4_plot = time_series_plot.plot(pen=pg.mkPen(color=(255,255,255), width=1))
        top_layout = QHBoxLayout()
        data_layout = QVBoxLayout()
        data_layout.addStretch(1)
        data_row1 = QHBoxLayout()
        data_row1.addWidget(QLabel("<font size=16>H<sub>2</sub>O<sub>2</sub></font>"))
        data_row1.addWidget(self.display_conc_h2o2)
        data_layout.addLayout(data_row1)
        data_layout.addStretch(1)
        data_row2 = QHBoxLayout()
        data_row2.addWidget(QLabel("<font size=16>CH<sub>4</sub></font>"))
        data_row2.addWidget(self.display_conc_ch4)
        data_layout.addLayout(data_row2)
        data_layout.addStretch(1)
        top_layout.addLayout(data_layout)
        top_layout.addWidget(time_series_plot)
        self.top_frame.setLayout(top_layout)
        
        self.wizard_frame = QWidget()
        self.display_caption = QLabel(validation_procedure[0][0])
        self.display_caption.setAccessibleName("caption")
        self.display_instruction = QLabel(validation_procedure[0][1])
        self.display_instruction.setAccessibleName("instruction")
        self.display_instruction.setFixedWidth(800)
        self.display_instruction.setFixedHeight(600)
        self.display_instruction.setWordWrap(True)
        self.input_nominal_concentration = QLineEdit()
        self.display_instruction2 = QLabel("Click Next to continue.")
        self.display_instruction2.setAccessibleName("instruction2")
        self.nominal_concentration = QWidget()
        self.nominal_concentration.hide()
        nominal_concentration_layout = QHBoxLayout()
        nominal_concentration_layout.addWidget(QLabel("<b>Nominal Concentration (ppm)</b>"))
        nominal_concentration_layout.addWidget(self.input_nominal_concentration)
        self.nominal_concentration.setLayout(nominal_concentration_layout)
        information_layout = QVBoxLayout()
        information_layout.addWidget(self.display_caption)
        information_layout.addWidget(self.display_instruction)
        information_layout.addWidget(self.display_instruction2)
        information_layout.addWidget(self.nominal_concentration)
        information_layout.addStretch(1)
                
        # control buttons
        self.button_next_step = QPushButton("Next")
        self.button_cancel_process = QPushButton("Cancel")
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_next_step)
        button_layout.addWidget(self.button_cancel_process)
        
        wizard_layout = QGridLayout()
        wizard_layout.setColumnStretch(0,1)
        wizard_layout.setColumnStretch(2,1)
        wizard_layout.addLayout(information_layout,0,1,Qt.AlignHCenter)
        wizard_layout.addLayout(button_layout,1,1,Qt.AlignHCenter)
        self.wizard_frame.setLayout(wizard_layout)
        
        # report 
        self.report_frame = QWidget()
        self.report = QTextEdit()
        self.report.setFixedWidth(800)
        self.report.setFixedHeight(800)
        self.report.setReadOnly(True)
        self.button_save_report = QPushButton("Save Report")
        self.button_cancel_report = QPushButton("Cancel")
        
        control_layout = QHBoxLayout()
        control_layout.addStretch(1)
        control_layout.addWidget(self.button_save_report)
        control_layout.addWidget(self.button_cancel_report)
        control_layout.addStretch(1)
        report_layout = QGridLayout()
        report_layout.setColumnStretch(0,1)
        report_layout.setColumnStretch(2,1)
        report_layout.addWidget(self.report,0,1,Qt.AlignHCenter)
        report_layout.addLayout(control_layout,1,1,Qt.AlignHCenter)
        self.report_frame.setLayout(report_layout)
        
        # login
        self.login_frame = QWidget()
        self.input_user_name = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)        
        self.button_user_login = QPushButton("Login")
        self.button_cancel_login = QPushButton("Cancel")
        self.label_login_info = QLabel("")
        login_input = QFormLayout()
        login_input.addRow("User Name", self.input_user_name)
        login_input.addRow("Password", self.input_password)
        login_buttons = QHBoxLayout()
        login_buttons.addWidget(self.button_user_login)
        login_buttons.addWidget(self.button_cancel_login)
        login_layout = QGridLayout()
        login_layout.setColumnStretch(0,1)
        login_layout.setColumnStretch(2,1)
        login_layout.setRowStretch(1,1)
        login_layout.addLayout(login_input,2,1,Qt.AlignHCenter)
        login_layout.addLayout(login_buttons,3,1,Qt.AlignHCenter)
        login_layout.addWidget(self.label_login_info,4,1,Qt.AlignHCenter)
        login_layout.setRowStretch(5,1)
        self.login_frame.setLayout(login_layout)
            
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_frame)
        main_layout.addWidget(self.wizard_frame)
        main_layout.addWidget(self.report_frame)
        main_layout.addWidget(self.login_frame)
        main_layout.addStretch(1)        
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self.report_frame.hide()
        self.top_frame.hide()
        self.wizard_frame.hide()
        
    def set_connections(self):
        self.measurement_timer.timeout.connect(self.measurement)
        self.button_next_step.clicked.connect(self.next_step)
        self.button_cancel_process.clicked.connect(self.cancel_process)
        self.button_save_report.clicked.connect(self.save_report)
        self.input_password.returnPressed.connect(self.user_login)
        self.button_user_login.clicked.connect(self.user_login)
        self.button_cancel_login.clicked.connect(self.cancel_login)
        
    def send_request(self, action, api, payload):
        """
        action: 'get' or 'post'
        """
        action_func = getattr(self.host_session, action)
        try:
            response = action_func(DB_SERVER_URL + api, data=payload)
            return response.json()
        except Exception, err:
            return {"error": str(err)}
        
    def user_login(self):
        payload = {'command': "log_in_user",
                   'requester': "H2O2Validation",
                   'username': str(self.input_user_name.text()), 
                   'password': str(self.input_password.text())}
        return_dict = self.send_request("post", "account", payload)
        if "error" not in return_dict:
            if "roles" in return_dict:
                if "Admin" in return_dict["roles"] or "Technician" in return_dict["roles"]:
                    self.input_user_name.clear()
                    self.input_password.clear()
                    self.current_user = return_dict
                    self.login_frame.hide()
                    self.top_frame.show()
                    self.wizard_frame.show()
                    if self.simulation:
                        self.simulation_thread = threading.Thread(target=self.run_simulation)
                        self.simulation_thread.daemon = True
                        self.simulation_thread.start()
                else:
                    self.label_login_info.setText("You don't have the permission to perform validation.")
                    self.send_request("post", "account", {"command":"log_out_user"})
        else:
            self.label_login_info.setText(return_dict["error"])
            
    def cancel_login(self):
        self.input_user_name.clear()
        self.input_password.clear()
        
    def measurement(self):
        current_time = time.time()
        if self.record_status == "":    # wait before collecting data
            if current_time - self.start_time >= self.wait_time_before_collection:
                # transition to data collection
                self.start_time = current_time
                self.record_status = validation_steps[self.current_step]
                self.display_instruction2.setText("Collecting data...")
        elif current_time - self.start_time >= self.data_collection_time:
            # data collection is done
            self.measurement_timer.stop()
            stage = self.record_status
            self.record_status = ""
            result_string = ""
            # calculate averages
            if len(self.validation_data[stage]) > 0:
                self.validation_results[stage+"_mean"] = np.average(self.validation_data[stage])
                self.validation_results[stage+"_sd"] = np.std(self.validation_data[stage])
                result_string += "Average CH4 = %.3f ppm. " % (self.validation_results[stage+"_mean"])
            if stage == "zero_air" and len(self.validation_data["H2O2"]) > 0:
                self.validation_results["h2o2_mean"] = np.average(self.validation_data["H2O2"])
                result_string += "Average H2O2 = %.3f ppm. " % (self.validation_results["h2o2_mean"])
            self.button_next_step.setEnabled(True)
            if self.current_step == len(validation_procedure) - 1:
                self.button_next_step.setText("Create Report")
                self.display_instruction2.setText(result_string)
            else:
                self.display_instruction2.setText(result_string+" Click Next to continue.")
        
    def next_step(self):
        if self.current_step < len(validation_procedure) - 1:
            self.current_step += 1
            self.display_caption.setText(validation_procedure[self.current_step][0]) 
            self.display_instruction.setText(validation_procedure[self.current_step][1])
            if self.current_step+1 in validation_steps and validation_steps[self.current_step+1].startswith("calibrant"):
                self.nominal_concentration.show()
                self.display_instruction2.clear()
                self.nominal_concentration.setEnabled(True)
                self.input_nominal_concentration.clear()
                self.input_nominal_concentration.setFocus()
            elif self.current_step in validation_steps:
                if self.current_step == self.zero_air_step:
                    self.validation_results["zero_air_nominal"] = 0
                else:
                    self.validation_results[validation_steps[self.current_step]+"_nominal"] = \
                        str(self.input_nominal_concentration.text())
                self.nominal_concentration.setEnabled(False)
                self.button_next_step.setEnabled(False)
                self.display_instruction2.setText("Waiting...")
                self.start_time = time.time()
                self.measurement_timer.start(1000)
        else:
            self.top_frame.hide()
            self.wizard_frame.hide()
            self.report_frame.show()
            self.create_report()
    
    def cancel_process(self):
        pass
        
    def data_analysis(self):
        # fake data used for testing
        # self.validation_results = dict(
            # zero_air_nominal=0, zero_air_mean=-0.064270241, zero_air_sd=0.068583138,
            # calibrant1_nominal=2.01, calibrant1_mean=1.984485907, calibrant1_sd=0.085401663,
            # calibrant2_nominal=10, calibrant2_mean=10.02599381, calibrant2_sd=0.071903936,
            # calibrant3_nominal=100.2, calibrant3_mean=99.8075018, calibrant3_sd=0.100870281
        # )
        
        # linear fitting
        labels = ["zero_air", "calibrant1", "calibrant2", "calibrant3"]
        xdata = [float(self.validation_results[i+"_nominal"]) for i in labels]
        ydata = [float(self.validation_results[i+"_mean"]) for i in labels]
        coeffs = np.polyfit(xdata, ydata, 1)
        self.validation_results["ch4_slope"] = format(coeffs[0], '.6f')
        self.validation_results["ch4_intercept"] = format(-coeffs[1], '.6f')
        self.validation_results["h2o2_equivalent"] = format(-coeffs[1]/70.0*1000.0, '.6f')
        yfit = np.poly1d(coeffs)(xdata)
        ybar = np.average(ydata)
        ssreg = np.sum((yfit - ybar)**2)
        sstot = np.sum((ydata - ybar)**2)
        self.validation_results["ch4_r2"] = format(ssreg / sstot, '.6f')
        # create image
        fig = plt.figure(figsize=(6, 5), facecolor=(1,1,1))
        ax = fig.gca()
        ax.plot(xdata, ydata, 'bo', xdata, yfit, 'r-')
        ax.grid('on')
        plt.title('Surrogate Gas Validation')
        plt.xlabel('Nominal CH4 ppm')
        plt.ylabel('Observed CH4 ppm')
        canvas = fig.canvas
        canvas.draw()
        size = canvas.size()
        width, height = size.width(), size.height()
        return QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        
    def create_report(self):
        image = self.data_analysis()
        html = file("ReportTemplate.html","r").read()
        # fill data in report
        html = html.replace("{date}", time.strftime("%Y-%m-%d"))
        html = html.replace("{time}", time.strftime("%H:%M:%S"))
        html = html.replace("{operator}", "%s %s" % (self.current_user["first_name"], self.current_user["last_name"]))
        html = html.replace("{username}", self.current_user["username"])
        for key in self.validation_results:
            html = html.replace("{%s}" % key, str(self.validation_results[key]))
        self.report.setText(html)
        cursor = self.report.textCursor()
        doc = self.report.document()    
        # insert image into document
        url = QUrl("mydata://report.png")
        doc.addResource( QTextDocument.ImageResource, url, QVariant(image))
        image_format = QTextImageFormat()
        image_format.setName(url.toString())
        cursor.movePosition(QTextCursor.End)
        cursor.insertImage(image_format)
        
    def save_report(self):
        info = """
        <p><b>You are about to sign a record electronically. This is the legal equivalent of a traditional handwritten signature.</b></p>
        <p>Click OK to sign and save the validation report.</p>
        """
        msg = QMessageBox(QMessageBox.Warning, "Electronic Signature", info, QMessageBox.Ok | QMessageBox.Cancel, self)
        if msg.exec_() == QMessageBox.Ok:
            printer = QPrinter(QPrinter.PrinterResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setPaperSize(QPrinter.B4)
            file_name = time.strftime("Validation_Report_%Y-%m-%d-%H-%M-%S.pdf")
            printer.setOutputFileName(os.path.join(self.report_dir, file_name))
            doc = self.report.document()
            doc.setPageSize(QSizeF(printer.pageRect().size()))   #This is necessary if you want to hide the page number
            doc.print_(printer)

HELP_STRING = """H2O2Validation.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./H2O2Validation.ini"
-s                   simulation mode
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s'
    longOpts = ["help", "debug"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = "H2O2Validation.ini"
    simulation = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        simulation = True
    return (configFile, simulation)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = H2O2ValidationFrame(*handleCommandSwitches())
    window.show()
    app.exec_()