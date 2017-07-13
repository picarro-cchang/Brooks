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
import Queue
from collections import deque

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from H2O2ValidationFrame import H2O2ValidationFrame
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import StringPickler, Listener
from Host.Common import SharedTypes

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

validation_steps = {2:"zero_air", 4:"calibrant1", 6:"calibrant2", 8:"calibrant3"}

validation_procedure = [
    ("Introduction to System Validation", """
        <p>This validation procedure is based on sequentially introducing zero air and two (or three) methane standards.
        The H2O2 signal in zero air will be measured to evaluate the zero offset for the spectroscopic model. 
        The methane concentrations in zero air and in each standard will be measured, and a linear regression 
        is calculated to demonstrate the linearity and zero accuracy of the analyzer. 
        </p>
        <p>Validation process takes 20-30 minutes. A report will be generated if validation passes.</p>
        <p><b>Required Supplies</b>
            <ul>
                <li>Cylinder of zero air (dry synthetic hydrocarbon-free air.)</li>
                <li>Two or three methane standard cylinders containing 2, 10, and 100 ppm of methane certified at +/- 2% composition accuracy.</li>
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
        <h2>1. Attach a regulator to the zero air source if not already installed, with the output pressure set to zero. 
            Open the cylinder valve and adjust the output line pressure upwards to 2-3 psi (0.1-0.2 bar). </h2>
        <h2>2. Attach the zero air line to the instrument.</h2>
    """),
    ("Zero-Air Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
    ("Calibrant 1: Preparation", """
        <h2>1. Attach a methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </h2>
        <h2>2. Enter nominal concentration of methane gas below. </h2>
    """),
    ("Calibrant 1 Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
    ("Calibrant 2: Preparation", """
        <h2>1. Attach a methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </h2>
        <h2>2. Enter nominal concentration of methane gas below. </h2>
    """),
    ("Calibrant 2 Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
    ("Calibrant 3: Preparation", """
        <h2>1. Attach a methane calibrant gas line at 2-3 psi (0.1-0.2 bar). </h2>
        <h2>2. Enter nominal concentration of methane gas below. </h2>
    """),
    ("Calibrant 3 Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
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

class H2O2Validation(H2O2ValidationFrame):
    def __init__(self, configFile, simulation=False, no_login=False, parent=None):
        if not os.path.exists(configFile):
            print "Config file not found: %s" % configFile
            sys.exit(0)
        self.config = CustomConfigObj(configFile)
        self.simulation = simulation
        super(H2O2Validation, self).__init__(parent)
        self.load_config()
        self.display_caption.setText(validation_procedure[0][0])
        self.display_instruction.setText(validation_procedure[0][1])
        self.host_session = requests.Session()
        self.current_step = 0
        self.start_time = 0
        self.record_status = ""
        self.zero_air_step = validation_steps.keys()[validation_steps.values().index("zero_air")]
        self.validation_data = {}        
        self.validation_results = {}
        self.data_queue = Queue.Queue()
        self.ch4_data = TimeSeriesData(100)
        self.data_fields = ["CH4", "H2O", "H2O2", "CavityPressure", "CavityTemp"]
        for k in validation_steps:
            step = validation_steps[k] 
            self.validation_data[step] = {"time": []}
            for field in self.data_fields:
                self.validation_data[step][field] = []
        
        if self.simulation:
            self.simulation_env = {func: getattr(math, func) for func in dir(math) if not func.startswith("__")}
            self.simulation_env.update({'random':  random.random, 'x': 0})
        if no_login:
            self.current_user = {"first_name": "Picarro", "last_name": "Testing", "username": "test", "token": ""}
            self.login_frame.hide()
            self.top_frame.show()
            self.wizard_frame.show()
            self.start_data_collection()
        # self.top_frame.hide()
        # self.wizard_frame.hide()
        # self.report_frame.show()
        # self.create_report()
            
    def load_config(self):
        self.update_period = self.config.getfloat("Setup", "Update_Period")
        self.wait_time_before_collection = self.config.getint("Setup", "Wait_Time_before_Data_Collection")
        self.data_collection_time = self.config.getint("Setup", "Data_Collection_Time")
        self.total_measurement_time = self.wait_time_before_collection + self.data_collection_time
        self.report_dir = self.config.get("Setup", "Report_Directory")
        if not os.path.isabs(self.report_dir):
            self.report_dir = os.path.join(self.curr_dir, self.report_dir)
        self.average_data_point = self.config.getint("Status_Check", "Average_Data_Points", 10)
        self.water_conc_limit = self.config.getfloat("Status_Check", "Water_Conc_Limit", 100)
        self.pressure_upper_limit = self.config.getfloat("Status_Check", "Pressure_Upper_Limit", 1000)
        self.pressure_lower_limit = self.config.getfloat("Status_Check", "Pressure_Lower_Limit", 0)
        self.temperature_upper_limit = self.config.getfloat("Status_Check", "Temperature_Upper_Limit", 1000)
        self.temperature_lower_limit = self.config.getfloat("Status_Check", "Temperature_Lower_Limit", -1000)
        self.ch4_max_deviation = self.config.getfloat("Status_Check", "CH4_Max_Deviation_Absolute", 1)
        self.ch4_max_deviation_percent = self.config.getfloat("Status_Check", "CH4_Max_Deviaion_Percent", 1000)/100.0  
        self.ch4_max_std = self.config.getfloat("Status_Check", "CH4_Max_STD_Absolute", 0.1)
        self.ch4_max_std_percent = self.config.getfloat("Status_Check", "CH4_Max_STD_Percent", 0.1)/100.0 
        if self.simulation:
            self.simulation_dict = dict(
                H2O2=self.config.get("Simulation", "H2O2", "0.0"),
                CH4=self.config.get("Simulation", "CH4", "0.0"),
                H2O=self.config.get("Simulation", "H2O", "0.0"),
                CavityPressure=self.config.get("Simulation", "CavityPressure", "0.0"),
                CavityTemp=self.config.get("Simulation", "CavityTemp", "0.0"),
                CH4_zero_air=self.config.get("Simulation", "CH4_zero_air", "0.0"),
                CH4_calibrant1=self.config.get("Simulation", "CH4_calibrant1", None),
                CH4_calibrant2=self.config.get("Simulation", "CH4_calibrant2", None),
                CH4_calibrant3=self.config.get("Simulation", "CH4_calibrant3", None)
            )
            self.ch4_simulation = self.simulation_dict["CH4"]
            
    def start_data_collection(self):
        if self.simulation:
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
        else:
            self.listener = Listener.Listener(None,
                                             SharedTypes.BROADCAST_PORT_DATA_MANAGER,
                                             StringPickler.ArbitraryObject,
                                             self.stream_filter,
                                             retry = True,
                                             name = "H2O2Validation")
        self.measurement_timer.start(int(self.update_period*1000))

    def message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(icon, title, message, buttons, self)
        return msg_box.exec_()
        
    def stream_filter(self, entry):
        if entry["source"] == "analyze_H2O2":
            try:
                data = {c: entry['data'][c] for c in self.data_fields}
                self.process_data(entry['data']['time'], data)
            except:
                pass
    
    def run_simulation(self):
        while True:
            if self.current_step in validation_steps:
                step = "CH4_%s" % (validation_steps[self.current_step])
                if self.simulation_dict[step] is not None:
                    self.ch4_simulation = self.simulation_dict[step]
            data = {}
            data["CH4"] = self.run_simulation_expression(self.ch4_simulation)
            data["H2O2"] = self.run_simulation_expression(self.simulation_dict['H2O2'])
            data["H2O"] = self.run_simulation_expression(self.simulation_dict['H2O'])
            data["CavityPressure"] = self.run_simulation_expression(self.simulation_dict['CavityPressure'])
            data["CavityTemp"] = self.run_simulation_expression(self.simulation_dict['CavityTemp'])
            self.process_data(time.time(), data)
            self.simulation_env['x'] += 1
            time.sleep(self.update_period)            
            
    def process_data(self, xdata, ydata):
        self.data_queue.put([xdata, ydata["CH4"], ydata["H2O2"], ydata["H2O"]])
        if len(self.record_status) > 0 and not self.record_status.startswith("error"):
            # save data
            for field in self.data_fields:
                self.validation_data[self.record_status][field].append(ydata[field])
            self.validation_data[self.record_status]['time'].append(xdata)            
            self.check_status(self.record_status)

    def check_status(self, stage):        
        if self.check_status_variable(stage, "H2O", lambda x: x > self.water_conc_limit,
                "Water concentration is too high!\nPlease check gas source!"):
            return 1
        if self.check_status_variable(stage, "CavityPressure",
                lambda x: x > self.pressure_upper_limit or x < self.pressure_lower_limit,
                "Cavity pressure is out of range!\nPlease check gas source and pump!"):
            return 1
        if self.check_status_variable(stage, "CavityTemp",
                lambda x: x > self.temperature_upper_limit or x < self.temperature_lower_limit,
                "Cavity temperature is out of range!\nPlease check analyzer!"):
            return 1
                
    def check_status_variable(self, stage, variable, criteria, error_info):
        var = self.validation_data[stage][variable]
        if len(var) > self.average_data_point:
            avg = np.average(var[-self.average_data_point:])
            if criteria(avg):
                self.record_status = "error|%s|%s" % (self.record_status, error_info)
                return 1
        return 0
            
    def run_simulation_expression(self, expression):
        if len(expression) > 0:
            exec "simulation_result=" + expression in self.simulation_env
            return self.simulation_env["simulation_result"]
        else:
            return 0.0 

    def send_request(self, action, api, payload, use_token=False):
        """
        action: 'get' or 'post'
        use_token: set to True if the api requires token for authentication
        """
        if use_token:
            header = {'Authentication': self.current_user["token"]}
        else:
            header = {}
        return self._send_request(action, api, payload, header)

    def _send_request(self, action, api, payload, header):
        action_func = getattr(self.host_session, action)
        try:
            response = action_func(DB_SERVER_URL + api, data=payload, headers=header)
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
                    self.start_data_collection()
                else:
                    self.label_login_info.setText("You don't have the permission to perform validation.")
                    self.send_request("post", "account", {"command":"log_out_user"})
        elif "Password expire" in return_dict["error"]:
            msg = "Password already expires!\nPlease use QuickGUI or other programs to change password."
            self.label_login_info.setText(msg)
        else:
            self.label_login_info.setText(return_dict["error"])
            
    def cancel_login(self):
        self.close()
        
    def measurement(self):
        # get data from queue and display
        x, ch4, h2o2, h2o = None, None, None, None
        while not self.data_queue.empty():
            x, ch4, h2o2, h2o = self.data_queue.get()
        if x is not None:
            self.display_conc_ch4.setText("%.3f" % ch4)
            self.display_conc_h2o2.setText("%.3f" % h2o2)
            self.display_conc_h2o.setText("%.3f" % h2o)
            self.ch4_data.put(x, ch4)
            self.ch4_plot.setData(*self.ch4_data.get())
        if self.start_time > 0:
            current_time = time.time()
            dt = current_time - self.start_time
            if self.record_status == "":    # wait before collecting data
                self.measurement_progress.setValue(int(dt*100/self.total_measurement_time))
                if dt >= self.wait_time_before_collection:
                    # transition to data collection
                    self.start_time = current_time
                    self.record_status = validation_steps[self.current_step]
                    self.display_instruction2.setText("Collecting data...")
            elif self.record_status.startswith("error"):
                self.start_time = 0
                self.measurement_progress.hide()
                stage, info = self.record_status.split("|")[1:]
                self.record_status = ""
                self.message_box(QMessageBox.Critical, "Error", info)
                self.handle_measurement_error(stage)
            else:
                self.measurement_progress.setValue(
                    int((dt+self.wait_time_before_collection)*100/self.total_measurement_time))
                if dt >= self.data_collection_time:
                    # data collection is done
                    self.start_time = 0
                    stage = self.record_status
                    self.record_status = ""
                    result_string = ""
                    # calculate averages
                    if len(self.validation_data[stage]["CH4"]) > 0:
                        avg = np.average(self.validation_data[stage]["CH4"])
                        nominal = self.validation_results[stage+"_nominal"]
                        std = np.std(self.validation_data[stage]["CH4"])
                        if self.check_ch4_result(nominal, avg, std, stage):
                            return 1
                        self.validation_results["%s_ch4_mean" % stage] = avg
                        self.validation_results["%s_ch4_sd" % stage] = std
                        self.validation_results["%s_ch4_diff" % stage] = avg - nominal
                        result_string += "Average CH4 = %.3f ppm. " % (self.validation_results[stage+"_ch4_mean"])
                    if len(self.validation_data[stage]["H2O2"]) > 0:
                        self.validation_results["%s_h2o2_mean" % stage] = np.average(self.validation_data[stage]["H2O2"])
                        result_string += "Average H2O2 = %.3f ppm. " % (self.validation_results["%s_h2o2_mean" % stage])
                        self.validation_results["%s_h2o_mean" % stage] = np.average(self.validation_data[stage]["H2O"])
                    self.button_next_step.setEnabled(True)
                    self.measurement_progress.hide()
                    if self.current_step == len(validation_procedure) - 1:
                        self.button_next_step.setText("Create Report")
                        self.button_next_step.setStyleSheet("width: 110px")
                        self.display_instruction2.setText("Data collection is done. Ready to create report.")
                    else:
                        self.display_instruction2.setText("Click Next to continue.")
                    self.message_box(QMessageBox.Information, "Measurement Done", result_string)
                
    def handle_measurement_error(self, step_name):
        # clear data collected in this step
        for k in self.validation_data[step_name]:
            self.validation_data[step_name][k] = []        
        # go to previous step so user have time to fix problem
        self.current_step -= 2
        self.button_next_step.setEnabled(True)
        self.display_instruction2.clear()
        self.measurement_progress.hide()
        self.next_step()
                
    def check_ch4_result(self, nominal, average, std, step_name):
        if nominal > 0:
            deviation = abs(average - nominal)/nominal
            deviation_limit = self.ch4_max_deviation_percent
            std_limit = nominal*self.ch4_max_std_percent
        else:
            deviation = abs(average)
            deviation_limit = self.ch4_max_deviation
            std_limit = self.ch4_max_std
        if deviation > deviation_limit:
            info = "Nominal concentration = %s\nAveraged CH4 concentration = %s\n" + \
                "Measurement result is too far away from nominal concentration!\n" + \
                "Click OK to run this step again.\nClick Cancel to ignore this error and proceed to next step."
            info = info % (nominal, average)
            ret = self.message_box(QMessageBox.Critical, "Error", info, QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
                self.handle_measurement_error(step_name)
                return 1
        if std > std_limit:
            info = ("Standard deviation = %s\n" % std) + \
                "Measurement data is too noisy\nPlease check analyzer."
            self.message_box(QMessageBox.Critical, "Error", info)
            self.handle_measurement_error(step_name)
            return 1
        return 0

    def skip_step(self):
        info = "Do you really want to skip the 3rd calibrant?"
        ret = self.message_box(QMessageBox.Question, "Skip Step", info, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            self.button_skip_step.hide()
            self.current_step += 1
            self.button_next_step.setText("Create Report")
            self.button_next_step.setStyleSheet("width: 110px")
            self.display_instruction2.setText("Data collection is done. Ready to create report.")
        
    def next_step(self):
        if self.current_step < len(validation_procedure) - 1:
            self.current_step += 1
            if self.current_step+1 in validation_steps and validation_steps[self.current_step+1].startswith("calibrant"):
                self.nominal_concentration.show()
                self.display_instruction2.clear()
                self.nominal_concentration.setEnabled(True)
                if validation_steps[self.current_step+1] == "calibrant3":
                    self.button_skip_step.show()
                self.input_nominal_concentration.clear()
                self.input_nominal_concentration.setFocus()
            elif self.current_step in validation_steps:
                if self.current_step == self.zero_air_step:
                    self.validation_results["zero_air_nominal"] = 0
                else:
                    
                    try:
                        concentration = float(self.input_nominal_concentration.text())
                    except ValueError:
                        msg = "Not a valid nomial concentration!"
                        self.message_box(QMessageBox.Critical, "Error", msg)
                        self.current_step -= 1
                        return 1
                    self.validation_results[validation_steps[self.current_step]+"_nominal"] = concentration
                self.nominal_concentration.setEnabled(False)
                self.button_next_step.setEnabled(False)
                self.button_skip_step.hide()
                self.display_instruction2.setText("Waiting...")
                self.measurement_progress.setValue(0)
                self.measurement_progress.show()
                self.start_time = time.time()
            self.display_caption.setText(validation_procedure[self.current_step][0]) 
            self.display_instruction.setText(validation_procedure[self.current_step][1])
        else:
            self.top_frame.hide()
            self.wizard_frame.hide()
            self.report_frame.show()
            self.create_report()
    
    def cancel_process(self):
        msg = "Do you really want to abort validation process?"
        ret = self.message_box(QMessageBox.Question, "Stop Validation", msg, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            payload = {"command": "save_action",
                       "username": self.current_user["username"],
                       "action": "Abort H2O2 validation"}
            self.send_request("post", "action", payload)
            self.close()

    def data_analysis(self):
        # fake data used for testing
        # self.validation_results = dict(
        #     zero_air_nominal=0, zero_air_ch4_mean=-0.064, zero_air_ch4_sd=0.0685,
        #     zero_air_ch4_diff=0.001, zero_air_h2o2_mean=0.001, zero_air_h2o_mean=0.001,
        #     calibrant1_nominal=2, calibrant1_ch4_mean=1.984, calibrant1_ch4_sd=0.0854,
        #     calibrant1_ch4_diff=0.001, calibrant1_h2o2_mean=0.001, calibrant1_h2o_mean=0.001,
        #     calibrant2_nominal=10, calibrant2_ch4_mean=10.025, calibrant2_ch4_sd=0.0719,
        #     calibrant2_ch4_diff=0.001, calibrant2_h2o2_mean=0.001, calibrant2_h2o_mean=0.001,
        #     calibrant3_nominal=100.2, calibrant3_ch4_mean=99.807, calibrant3_ch4_sd=0.1008,
        #     calibrant3_ch4_diff=0.001, calibrant3_h2o2_mean=0.001, calibrant3_h2o_mean=0.001,
        #     status_ch4_slope="<font color='green'>Pass</font>",
        #     status_zero_h2o2="<font color='green'>Pass</font>",
        #     status_ch4_r2="<font color='green'>Pass</font>"
        # )
        
        # linear fitting
        self.step_names = ["zero_air", "calibrant1", "calibrant2"]
        if "calibrant3_ch4_mean" in self.validation_results:
            self.step_names.append("calibrant3")
            self.validation_results["calibrant3_source"] = "Calibrant 3"     
        xdata = [self.validation_results[i+"_nominal"] for i in self.step_names]
        ydata = [self.validation_results[i+"_ch4_mean"] for i in self.step_names]
        coeffs = np.polyfit(xdata, ydata, 1)
        self.validation_results["ch4_slope"] = coeffs[0]
        self.validation_results["ch4_intercept"] = -coeffs[1]
        self.validation_results["h2o2_equivalent"] = -coeffs[1]/70.0*1000.0
        yfit = np.poly1d(coeffs)(xdata)
        ybar = np.average(ydata)
        ssreg = np.sum((yfit - ybar)**2)
        sstot = np.sum((ydata - ybar)**2)
        self.validation_results["ch4_r2"] = ssreg / sstot
        # create image1: observed ch4 vs nominal ch4
        image1 = self.create_image(xdata, ydata, yfit, 
            'Surrogate Gas Validation', 'Nominal CH4 ppm', 'Observed CH4 ppm')        

        # create image2: observed h2o2 vs nomial h2o2
        nominal_h2o2 = [self.validation_results[s+"_nominal"]/70.0*1000.0 for s in self.step_names]
        observed_h2o2 = [self.validation_results[s+"_ch4_mean"]/70.0*1000.0 for s in self.step_names]
        coeffs = np.polyfit(nominal_h2o2, observed_h2o2, 1)
        yfit2 = np.poly1d(coeffs)(nominal_h2o2)
        image2 = self.create_image(nominal_h2o2, observed_h2o2, yfit2,
            'Surrogate Gas Validation', 'Nominal Equivalent H2O2 ppb', 'Observed Equivalent H2O2 ppb')
        return [image1, image2]

    def create_image(self, xdata, ydata, yfitting, title, xlabel, ylabel):
        fig = plt.figure(figsize=(6, 5), facecolor=(1,1,1))
        ax = fig.gca()
        ax.plot(xdata, ydata, 'bo', xdata, yfitting, 'r-')
        ax.grid('on')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        max_x, min_x = max(xdata), min(xdata)
        offset = (max_x - min_x) * 0.05
        ax.set_xlim([min_x-offset, max_x+offset])
        ax.set_ylim([min_x-offset, max_x+offset])
        canvas = fig.canvas
        canvas.draw()
        size = canvas.size()
        width, height = size.width(), size.height()
        return QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        
    def create_report(self):
        imagelist = self.data_analysis()
        self.check_report()
        html = file(os.path.join(self.curr_dir, "ReportTemplate.html"),"r").read()
        # fill data in report
        items = ["source", "nominal", "ch4_mean", "ch4_sd", "ch4_diff", "h2o2_mean", "h2o_mean"]
        for item in items:
            html = html.replace("{%s}" % ("more_"+item), \
                ("<td>{%s}</td>" % ("calibrant3_"+item)) \
                if "calibrant3_ch4_mean" in self.validation_results else "")
        html = html.replace("{analyzer_name}", os.uname()[1])
        html = html.replace("{date}", time.strftime("%Y-%m-%d"))
        time_str = "%s (GMT%+d)" % (time.strftime("%H:%M:%S"), time.timezone/36)
        html = html.replace("{time}", time_str)
        html = html.replace("{operator}", "%s %s" % (self.current_user["first_name"], self.current_user["last_name"]))
        html = html.replace("{username}", self.current_user["username"])
        for key in self.validation_results:
            html = html.replace("{%s}" % key, self.format_variable(key))
        self.report.setText(html)
        cursor = self.report.textCursor()
        doc = self.report.document()
        # insert images into document
        for idx in range(len(imagelist)):
            url = QUrl("mydata://report%d.png" % idx)
            doc.addResource( QTextDocument.ImageResource, url, QVariant(imagelist[idx]))
            image_format = QTextImageFormat()
            image_format.setName(url.toString())
            cursor.movePosition(QTextCursor.End)
            cursor.insertImage(image_format)        

    def check_report(self):
        # check validation pass or fail
        errors = []
        if abs(self.validation_results["ch4_slope"] - 1) > 0.05:
            errors.append("CH4 slope (%s) is too far away from 1" % (self.validation_results["ch4_slope"]))
            self.validation_results["status_ch4_slope"] = "<font color='red'>Fail</font>"
        else:
            self.validation_results["status_ch4_slope"] = "<font color='green'>Pass</font>"
        if abs(self.validation_results["h2o2_equivalent"]) > 10:
            errors.append("Zero H2O2 (%s) is too far away from 0" % (self.validation_results["h2o2_equivalent"]))
            self.validation_results["status_zero_h2o2"] = "<font color='red'>Fail</font>"
        else:
            self.validation_results["status_zero_h2o2"] = "<font color='green'>Pass</font>"
        if self.validation_results["ch4_r2"] < 0.95:
            errors.append("Linearity (%s) is too low" % (self.validation_results["ch4_r2"]))
            self.validation_results["status_ch4_r2"] = "<font color='red'>Fail</font>"
        else:
            self.validation_results["status_ch4_r2"] = "<font color='green'>Pass</font>"
        if len(errors) > 0:
            msg = "Validation fails! See errors below:\n" + ("\n".join(errors))
            self.message_box(QMessageBox.Critical, "Validation Fail", msg)

    def format_variable(self, var_name):
        value = self.validation_results[var_name]
        end = var_name.split("_")[-1]
        if type(value) is str:
            return value
        elif end in ["mean", "diff", "intercept", "nominal"]:
            return format(value, ".3f")
        elif end == "sd":
            return format(value, ".4f")
        elif end == "equivalent":
            return format(value, ".2f")
        else:
            return format(value, ".6f")
        
    def save_report(self):
        msg = """
        <p><b>You are about to sign a record electronically. This is the legal equivalent of a traditional handwritten signature.</b></p>
        <p>Click OK to sign and save the validation report.</p>
        """
        ret = self.message_box(QMessageBox.Warning, "Electronic Signature", msg, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            printer = QPrinter(QPrinter.PrinterResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setPaperSize(QPrinter.B4)
            folder_name = time.strftime("%Y%m%d_%H%M%S")
            data_folder = os.path.join(self.curr_dir, folder_name)
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            file_name = time.strftime("Validation_Report_%Y-%m-%d-%H-%M-%S.pdf")
            printer.setOutputFileName(os.path.join(self.report_dir, folder_name, file_name))
            doc = self.report.document()
            doc.setPageSize(QSizeF(printer.pageRect().size()))   #This is necessary if you want to hide the page number
            doc.print_(printer)
            payload = {"username": self.current_user["username"],
                       "action": "Create validation report: %s" % (os.path.join(folder_name, file_name))}
            self.send_request("post", "action", payload, use_token=True)
            # save data files
            for step in self.step_names:
                with open(os.path.join(data_folder, step+".csv"), "w") as f:
                    f.write("Time, " + ", ".join(self.data_fields) + "\n")
                    for idx in xrange(len(self.validation_data[step]['time'])):
                        f.write(str(self.validation_data[step]['time'][idx]))
                        for field in self.data_fields:
                            f.write(", %s" % (self.validation_data[step][field][idx]))
                        f.write("\n")
            msg = "Validation report created: %s\nThis program will be closed." % file_name
            self.message_box(QMessageBox.Information, "Save Report", msg)
            self.close()

    def cancel_report(self):
        msg = "Do you really want to quit the program without saving report?"
        ret = self.message_box(QMessageBox.Question, "Quit Program", msg, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            payload = {"command": "save_action",
                       "username": self.current_user["username"],
                       "action": "Quit H2O2 validation without saving report"}
            self.send_request("post", "action", payload, use_token=True)
            self.close()

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
    longOpts = ["help", "no_login"]
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
    no_login = False
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        simulation = True
    if "--no_login" in options: # used for testing program without sqlite server
        no_login = True
    return (configFile, simulation, no_login)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = H2O2Validation(*handleCommandSwitches())
    window.show()
    app.exec_()