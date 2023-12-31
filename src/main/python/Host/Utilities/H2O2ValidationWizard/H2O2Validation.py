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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from H2O2ValidationFrame import H2O2ValidationFrame
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common import StringPickler, Listener
from Host.Common import SharedTypes
from Host.Common.SingleInstance import SingleInstance

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

validation_steps = {2: "zero_air", 4: "calibrant1", 6: "calibrant2", 8: "calibrant3"}

validation_procedure = [("Introduction to System Validation", """
        <p>This validation procedure is based on sequentially introducing zero air and three methane standards.
        The H2O2 signal in zero air will be measured to evaluate the zero offset for the spectroscopic model. 
        The methane concentrations in zero air and in each standard will be measured, and a linear regression 
        is calculated to demonstrate the linearity and zero accuracy of the analyzer. 
        </p>
        <p>The validation process takes 20-30 minutes. A PDF report with electronic signature will be generated upon successful completion.</p>
        <p><b>Required Supplies</b>
            <ul>
                <li>Cylinder of zero air (dry synthetic hydrocarbon-free air).</li>
                <li>Three methane standard cylinders containing 2, 10, and 100 ppm of methane certified at +/- 2% composition accuracy or better.</li>
                <li>Two-stage regulators for each gas cyclinder capable of accurately delivering 2-3 psi (0.1-0.2 bar) of line pressure.</li>
                <li>Sufficient tubing to connect the regulators to the instrument. </li>
                <li>1/4" Swagelok Ultra-Torr fittings for the gas lines.</li>
            </ul>
        </p>
        <p><b>Safety</b><br>
        At the concentrations used here, methane poses zero health, reactivity, or flammability risks. 
        Follow all safety conventions appropriate for work with compressed gases, including use of eye protection, physical restraint of cylinders, etc.
        </p>
    """),
                        ("Zero-Air Measurement: Preparation", """
        <h2>1. Attach a regulator to the zero air source with the output pressure set to zero. 
            Open the cylinder valve and adjust the output line pressure to 2-3 psig (0.1-0.2 bar). </h2>
        <h2>2. Attach the zero air line to the instrument.</h2>
        <h2>3. Select the zero-air cylinder from the drop down menu.  If a zero-air cylinder does not appear as an option, click EDIT CYLINDERS to enter in the information about your zero-air cylinder.</h2>
        <h2>4. After selecting a zero-air source, click NEXT.
    """),
                        ("Zero-Air Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
                        ("Calibrant 1: Preparation", """
        <h2>1. Remove the previous cylinder.</h2>
        <h2>2. Set the output pressure of lowest concentration methane cylinder to 2-3 psi.</h2>
        <h2>3. Attach the lowest methane concentration cylinder to the instrument.</h2>
        <h2>4. Select the appropriate cylinder from the drop down menu.</h2>
        <h2>5. Click NEXT to continue.</h2>
    """),
                        ("Calibrant 1 Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
                        ("Calibrant 2: Preparation", """
        <h2>1. Remove the previous cylinder.</h2>
        <h2>2. Set the output pressure of mid-range concentration methane cylinder to 2-3 psi.</h2>
        <h2>3. Attach the mid-range methane concentration cylinder to the instrument.</h2>
        <h2>4. Select the appropriate cylinder from the drop down menu.</h2>
        <h2>5. Click NEXT to continue.</h2>
    """),
                        ("Calibrant 2 Measurement", """
        <h2>Data Collection</h2>
        <h3>This process will take a few minutes...</h3>
    """),
                        ("Calibrant 3: Preparation", """
        <h2>1. Remove the previous cylinder.</h2>
        <h2>2. Set the output pressure of highest concentration methane cylinder to 2-3 psi.</h2>
        <h2>3. Attach the highest methane concentration cylinder to the instrument.</h2>
        <h2>4. Select the appropriate cylinder from the drop down menu.</h2>
        <h2>5. Click NEXT to continue.</h2>
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
        self.cylinder_reviewed = False
        self.system_ready = False
        self.zero_air_step = validation_steps.keys()[validation_steps.values().index("zero_air")]
        self.validation_data = {}
        self.validation_results = {}
        self.cylinder_used = {}
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
            self.simulation_env.update({'random': random.random, 'x': 0})
        if no_login:
            self.current_user = {
                "first_name": "Picarro",
                "last_name": "Testing",
                "username": "test",
                "token": "",
                "login_time": time.time()
            }
            self.login_frame.hide()
            self.top_frame.show()
            self.wizard_frame.show()
            self.start_data_collection()

    def load_config(self):
        self.cylinders = {}
        self.cylinder_list_file = self.config.get("Setup", "Cylinder_List")
        if not os.path.isabs(self.cylinder_list_file):
            self.cylinder_list_file = os.path.join(self.curr_dir, self.cylinder_list_file)
        if not os.path.exists(self.cylinder_list_file):
            open(self.cylinder_list_file, 'w').close()
        self.cylinder_config = CustomConfigObj(self.cylinder_list_file)
        for section in self.cylinder_config:
            if self.cylinder_config.getboolean(section, "Active", False):
                self.cylinders[section] = {
                    "concentration": self.cylinder_config.getfloat(section, "Concentration"),
                    "uncertainty": self.cylinder_config.getfloat(section, "Uncertainty")
                }
        self.update_period = self.config.getfloat("Setup", "Update_Period")
        self.wait_time_before_collection = self.config.getint("Setup", "Wait_Time_before_Data_Collection")
        self.data_collection_time = self.config.getint("Setup", "Data_Collection_Time")
        self.total_measurement_time = self.wait_time_before_collection + self.data_collection_time
        # Determine whether or not calibrant3 can be skipped.
        # Disable this option to force users measure 3 calibrants.
        self.allow_skip_calibrant3 = False  #self.config.getboolean("Setup", "Allow_Skip_Calibrant3")
        self.report_dir = self.config.get("Setup", "Report_Directory")
        if not os.path.isabs(self.report_dir):
            self.report_dir = os.path.join(self.curr_dir, self.report_dir)
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
        self.average_data_point = self.config.getint("Status_Check", "Average_Data_Points", 10)
        self.water_conc_limit = self.config.getfloat("Status_Check", "Water_Conc_Limit")
        self.pressure_upper_limit = self.config.getfloat("Status_Check", "Pressure_Upper_Limit", 1000)
        self.pressure_lower_limit = self.config.getfloat("Status_Check", "Pressure_Lower_Limit", 0)
        self.temperature_upper_limit = self.config.getfloat("Status_Check", "Temperature_Upper_Limit", 1000)
        self.temperature_lower_limit = self.config.getfloat("Status_Check", "Temperature_Lower_Limit", -1000)
        self.ch4_max_deviation = self.config.getfloat("Status_Check", "CH4_Max_Deviation_Absolute", 1)
        self.ch4_max_deviation_percent = self.config.getfloat("Status_Check", "CH4_Max_Deviation_Percent", 10) / 100.0
        self.ch4_max_std = self.config.getfloat("Status_Check", "CH4_Max_STD_Absolute", 0.1)
        self.ch4_max_std_percent = self.config.getfloat("Status_Check", "CH4_Max_STD_Percent", 0.1) / 100.0
        if self.simulation:
            self.simulation_dict = dict(H2O2=self.config.get("Simulation", "H2O2", "0.0"),
                                        CH4=self.config.get("Simulation", "CH4", "0.0"),
                                        H2O=self.config.get("Simulation", "H2O", "0.0"),
                                        CavityPressure=self.config.get("Simulation", "CavityPressure", "0.0"),
                                        CavityTemp=self.config.get("Simulation", "CavityTemp", "0.0"),
                                        CH4_zero_air=self.config.get("Simulation", "CH4_zero_air", "0.0"),
                                        CH4_calibrant1=self.config.get("Simulation", "CH4_calibrant1", None),
                                        CH4_calibrant2=self.config.get("Simulation", "CH4_calibrant2", None),
                                        CH4_calibrant3=self.config.get("Simulation", "CH4_calibrant3", None))
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
                                              retry=True,
                                              name="H2O2Validation")
        self.measurement_timer.start(int(self.update_period * 1000))

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
        self.system_ready = True
        self.data_queue.put([xdata, ydata["CH4"], ydata["H2O2"], ydata["H2O"]])
        if len(self.record_status) > 0 and not self.record_status.startswith("error"):
            # save data
            for field in self.data_fields:
                self.validation_data[self.record_status][field].append(ydata[field])
            self.validation_data[self.record_status]['time'].append(xdata)

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
        payload = {
            'command': "log_in_user",
            'requester': "H2O2Validation",
            'username': str(self.input_user_name.text()),
            'password': str(self.input_password.text())
        }
        return_dict = self.send_request("post", "account", payload)
        if "error" not in return_dict:
            if "roles" in return_dict:
                if not hasattr(self, "current_user"):  # first-time login
                    self.input_user_name.clear()
                    self.input_password.clear()
                    self.current_user = return_dict
                    self.current_user["login_time"] = time.time()
                    self.login_frame.hide()
                    self.top_frame.show()
                    self.wizard_frame.show()
                    self.start_data_collection()
                else:  # login to sign report
                    self.signature_user = return_dict
                    self.login_frame.hide()
                    self.report_frame.show()
                    self.create_report()
                    self.save_report()
        elif "Password expire" in return_dict["error"]:
            msg = "Password already expires!\nPlease use QuickGUI or other programs to change password."
            self.label_login_info.setText(msg)
        else:
            if "HTTPConnection" in return_dict["error"]:
                msg = "Unable to connect database server!"
            else:
                msg = return_dict["error"]
            self.label_login_info.setText(msg)

    def cancel_login(self):
        if not hasattr(self, "current_user"):  # first-time login
            self.close()
        else:  # login to sign report
            self.login_frame.hide()
            self.top_frame.show()
            self.wizard_frame.show()

    def edit_cylinder(self):
        self.report_frame.hide()
        self.top_frame.hide()
        self.wizard_frame.hide()
        self.cylinder_frame.show()
        self.update_cylinder_list()

    def select_cylinder_from_table(self):
        indexes = self.table_cylinder_list.selectionModel().selectedRows()
        if len(indexes) > 0:
            cylinder = self.table_cylinder_list.item(indexes[0].row(), 0)
            if cylinder is not None:
                ident = str(cylinder.text())
                self.label_cylinder_ident.setText(ident)
                self.input_cylinder_ch4.setText(str(self.cylinders[ident]["concentration"]))
                self.input_cylinder_uncertainty.setText(str(self.cylinders[ident]["uncertainty"]))

    def add_cylinder(self):
        self.cylinder_frame.hide()
        self.add_cylinder_frame.show()
        self.input_add_cylinder_ident.setFocus()

    def add_cylinder_cancel(self):
        self.input_add_cylinder_ident.clear()
        self.input_add_cylinder_ch4.clear()
        self.input_add_cylinder_uncertainty.clear()
        self.cylinder_frame.show()
        self.add_cylinder_frame.hide()

    def add_cylinder_ok(self):
        ident = str(self.input_add_cylinder_ident.text()).strip()
        if len(ident) == 0:
            self.message_box(QMessageBox.Critical, "Error", "Cylinder identification is blank!")
            return 1
        if ident in self.cylinders:
            self.message_box(QMessageBox.Critical, "Error", "Cylinder already exists!")
            return 1
        try:
            conc = float(self.input_add_cylinder_ch4.text())
        except:
            self.message_box(QMessageBox.Critical, "Error", "CH4 concentration not valid!")
            return 1
        try:
            uncertainty = float(self.input_add_cylinder_uncertainty.text())
        except:
            self.message_box(QMessageBox.Critical, "Error", "Concentration uncertainty not valid!")
            return 1
        if not self.update_cylinder_info(ident, conc, uncertainty):
            return 1
        self.update_cylinder_list()
        payload = {
            "username": self.current_user["username"],
            "action": "H2O2Validation: add cylinder %s, CH4=%s, uncertainty=%s" % (ident, conc, uncertainty)
        }
        self.send_request("post", "action", payload, use_token=True)
        self.add_cylinder_cancel()

    def update_cylinder_list(self):
        num_rows = self.table_cylinder_list.rowCount()
        num_cylinder = len(self.cylinders)
        if num_cylinder > num_rows:
            for _ in range(num_cylinder - num_rows):
                self.table_cylinder_list.insertRow(0)
        elif num_cylinder < num_rows:
            for _ in range(num_rows - num_cylinder):
                self.table_cylinder_list.removeRow(0)
        for idx, ident in enumerate(self.cylinders):
            self.table_cylinder_list.setItem(idx, 0, QTableWidgetItem(ident))
            self.table_cylinder_list.setItem(idx, 1, QTableWidgetItem(format(self.cylinders[ident]["concentration"], ".2f")))
            self.table_cylinder_list.setItem(idx, 2, QTableWidgetItem("+/- " + format(self.cylinders[ident]["uncertainty"], ".2f")))
            self.table_cylinder_list.setItem(idx, 3,
                                             QTableWidgetItem(self.cylinder_used[ident] if ident in self.cylinder_used else ""))
        self.table_cylinder_list.selectRow(num_cylinder - 1)
        self.select_cylinder_from_table()

    def delete_cylinder(self):
        indexes = self.table_cylinder_list.selectionModel().selectedRows()
        if len(indexes) > 0:
            cylinder = self.table_cylinder_list.item(indexes[0].row(), 0)
            if cylinder is not None:
                ident = str(cylinder.text())
                if self.message_box(QMessageBox.Question, "Delete Cylinder", "Delete %s?" % ident,
                                    QMessageBox.Ok | QMessageBox.Cancel) == QMessageBox.Ok:
                    self.cylinders.pop(ident)
                    self.cylinder_config[ident]["Active"] = "False"
                    payload = {"username": self.current_user["username"], "action": "H2O2Validation: delete cylinder %s" % (ident)}
                    self.send_request("post", "action", payload, use_token=True)
                    self.update_cylinder_list()

    def update_cylinder(self):
        ident = str(self.label_cylinder_ident.text()).strip()
        try:
            conc = float(self.input_cylinder_ch4.text())
        except:
            self.message_box(QMessageBox.Critical, "Error", "CH4 concentration not valid!")
            return 1
        try:
            uncertainty = float(self.input_cylinder_uncertainty.text())
        except:
            self.message_box(QMessageBox.Critical, "Error", "Concentration uncertainty not valid!")
            return 1
        ret = self.message_box(QMessageBox.Question, "Update Cylinder Info",
                               "Update %s?\nCH4=%s\nUncertainty=%s" % (ident, conc, uncertainty),
                               QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            if not self.update_cylinder_info(ident, conc, uncertainty):
                return 1
            payload = {
                "username": self.current_user["username"],
                "action": "H2O2Validation: update cylinder %s, CH4=%s, uncertainty=%s" % (ident, conc, uncertainty)
            }
            self.send_request("post", "action", payload, use_token=True)
            self.update_cylinder_list()

    def update_cylinder_info(self, identification, conc, uncertainty):
        if conc < 0 or conc > 1e6:
            self.message_box(QMessageBox.Critical, "Error", "CH4 concentration is out of range!\nMin=0, Max=1e6.")
            return False
        if uncertainty < 0 or uncertainty > 100:
            self.message_box(QMessageBox.Critical, "Error", "Concentration uncertainty is out of range!\nMin=0, Max=100.")
            return False
        self.cylinders[identification] = {"concentration": conc, "uncertainty": uncertainty}
        self.cylinder_config[identification] = {"Concentration": str(conc), "Uncertainty": str(uncertainty), "Active": "True"}
        return True

    def exit_cylinder_setting(self):
        self.cylinder_config.write()  # write to file
        self.cylinder_frame.hide()
        self.top_frame.show()
        self.wizard_frame.show()
        self.popular_cylinder_selection_list()

    def popular_cylinder_selection_list(self):
        self.select_cylinder.clear()
        available_cylinder = []
        for cylinder in self.cylinders:
            if cylinder not in self.cylinder_used:
                if validation_steps[self.current_step+1] == "zero_air" \
                    and self.cylinders[cylinder]["concentration"] > 0:
                    continue
                elif self.cylinders[cylinder]["concentration"] == 0 \
                    and validation_steps[self.current_step+1] != "zero_air":
                    continue
                available_cylinder.append(
                    [cylinder, self.cylinders[cylinder]["concentration"], self.cylinders[cylinder]["uncertainty"]])
        if len(available_cylinder) == 0:
            self.message_box(QMessageBox.Critical, "Notice",
                             "No available gas sources for this step.\n" + "Please edit information of gas sources!")
        else:
            available_cylinder = sorted(available_cylinder, key=lambda x: x[1])
            for item in available_cylinder:
                self.select_cylinder.addItem("%s: CH4=%.2f ppm +/-%d%%" % (item[0], item[1], item[2]))

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
            if self.record_status == "":  # wait before collecting data
                self.measurement_progress.setValue(int(dt * 100 / self.total_measurement_time))
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
                self.measurement_progress.setValue(int((dt + self.wait_time_before_collection) * 100 / self.total_measurement_time))
                self.check_status(self.record_status)
                if dt >= self.data_collection_time:
                    # data collection is done
                    self.start_time = 0
                    stage = self.record_status
                    self.record_status = ""
                    result_string = ""
                    # calculate averages
                    if len(self.validation_data[stage]["CH4"]) > 5:
                        avg = np.average(self.validation_data[stage]["CH4"])
                        nominal = self.validation_results[stage + "_nominal"]
                        std = np.std(self.validation_data[stage]["CH4"])
                        if self.check_ch4_result(nominal, avg, std, stage):
                            return 1
                        self.validation_results["%s_ch4_mean" % stage] = avg
                        self.validation_results["%s_ch4_sd" % stage] = std
                        self.validation_results["%s_ch4_diff" % stage] = abs(avg - nominal)*100.0/nominal \
                             if nominal > 1e-6 else 'N/A'
                        result_string = "Measured average concentrations\n\n"
                        result_string += "%-6s=%8.3f ppm.\n" % ("CH4", self.validation_results[stage + "_ch4_mean"])
                    else:
                        self.message_box(
                            QMessageBox.Critical, "Error", """<h3>Not enough data points collected!</h3>
                               <p>Please check the analyzer.</p>
                            """)
                        self.handle_measurement_error(stage)
                        return 1
                    if len(self.validation_data[stage]["H2O2"]) > 0:
                        self.validation_results["%s_h2o2_mean" % stage] = np.average(self.validation_data[stage]["H2O2"])
                        result_string += "%-6s=%8.3f ppb." % ("H2O2", self.validation_results["%s_h2o2_mean" % stage])
                        self.validation_results["%s_h2o_mean" % stage] = np.average(self.validation_data[stage]["H2O"])
                    self.button_next_step.setEnabled(True)
                    self.measurement_progress.hide()
                    if self.current_step == len(validation_procedure) - 1:
                        self.button_next_step.hide()
                        self.display_instruction2.setText("Data collection is done. Ready to create and save report.")
                    else:
                        self.display_instruction2.setText("Click Next to continue.")
                    self.message_box(QMessageBox.Information, "Measurement Done", result_string)
                    self.next_step()

    def handle_measurement_error(self, step_name):
        # clear data collected in this step
        for k in self.validation_data[step_name]:
            self.validation_data[step_name][k] = []
        for c in self.cylinder_used:
            if self.cylinder_used[c] == step_name:
                self.cylinder_used.pop(c)
                break
        # go to previous step so user have time to fix problem
        self.current_step -= 2
        self.button_next_step.setEnabled(True)
        self.display_instruction2.clear()
        self.measurement_progress.hide()
        self.next_step()

    def check_ch4_result(self, nominal, average, std, step_name):
        if nominal > 0:
            deviation = abs(average - nominal) / nominal
            deviation_limit = self.ch4_max_deviation_percent
            std_limit = nominal * self.ch4_max_std_percent
        else:
            deviation = abs(average)
            deviation_limit = self.ch4_max_deviation
            std_limit = self.ch4_max_std
        if deviation > deviation_limit:
            info = "Nominal concentration = %s\nAveraged CH4 concentration = %s\n" + \
                "Measurement result is too far away from nominal concentration!\n" + \
                "Please check the gas concentration, regulator pressure, and gas lines.\n" + \
                "Click OK to run this step again."
            info = info % (nominal, average)
            ret = self.message_box(QMessageBox.Critical, "Error", info)
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
            self.button_next_step.hide()
            self.next_step()

    def last_step(self):
        if self.current_step in validation_steps:
            info = """<h3>Do you really want to go back to last step?</h3>
                <p>Data collected in this step will be cleared if go back to last step.</p>
            """
            ret = self.message_box(QMessageBox.Question, "Go Back", info, QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
                self.start_time = 0
                self.record_status = ""
                self.handle_measurement_error(validation_steps[self.current_step])
        elif self.current_step - 1 in validation_steps:
            stage = validation_steps[self.current_step - 1]
            info = """<h3>Do you really want to go back to last step?</h3>
                <p>This will go back to beginning of %s measurement and data collected for %s will be clearred.</p>
            """ % (stage, stage)
            ret = self.message_box(QMessageBox.Question, "Go Back", info, QMessageBox.Ok | QMessageBox.Cancel)
            if ret == QMessageBox.Ok:
                self.current_step -= 1
                self.handle_measurement_error(stage)
        elif self.current_step == 1:
            self.current_step = -1
            self.next_step()
            self.cylinder_selection.hide()
            self.button_last_step.setEnabled(False)

    def next_step(self):
        if self.current_step < len(validation_procedure) - 1:
            self.current_step += 1
            if self.current_step + 1 in validation_steps:
                self.display_instruction2.clear()
                self.cylinder_selection.setEnabled(True)
                if validation_steps[self.current_step + 1] == "calibrant3" and self.allow_skip_calibrant3:
                    self.button_skip_step.show()
                self.popular_cylinder_selection_list()
                self.cylinder_selection.show()
            elif self.current_step in validation_steps:
                cylinder = str(self.select_cylinder.currentText()).split(":")[0]
                if cylinder == "":
                    self.message_box(QMessageBox.Critical, "Error", "Please select a cylinder!")
                    self.current_step -= 1
                    return 1
                elif not self.system_ready:
                    self.message_box(
                        QMessageBox.Critical, "Error", """<h2>System is NOT ready for measurement!</h2>
                           <p>System may still be warming up. Please start measurement after CH4 concentration is 
                           already displayed on the top-left corner of this program.</p>
                        """)
                    self.current_step -= 1
                    return 1
                concentration = self.cylinders[cylinder]["concentration"]
                uncertainty = self.cylinders[cylinder]["uncertainty"]
                stage = validation_steps[self.current_step]
                self.validation_results[stage + "_source"] = cylinder
                self.validation_results[stage + "_nominal"] = concentration
                self.validation_results[stage + "_info"] = "%s&plusmn;%s%%" % (concentration, uncertainty)
                self.cylinder_used[cylinder] = stage
                self.cylinder_selection.setEnabled(False)
                self.button_next_step.setEnabled(False)
                self.button_skip_step.hide()
                self.display_instruction2.setText("Waiting...")
                self.measurement_progress.setValue(0)
                self.measurement_progress.show()
                self.start_time = time.time()
            self.display_caption.setText(validation_procedure[self.current_step][0])
            self.display_instruction.setText(validation_procedure[self.current_step][1])
            self.button_last_step.setEnabled(True)
        else:
            self.label_login_message.setText("""
            <p>Measurement is done. Please login to sign and save the validation report.</p>
            <p>
                <b>You are about to sign a record electronically. 
                This is the legal equivalent of a traditional handwritten signature.</b>
            </p>            
            """)
            self.top_frame.hide()
            self.wizard_frame.hide()
            self.login_frame.show()
            self.input_user_name.clear()
            self.input_password.clear()
            self.input_user_name.setFocus()
        if not self.cylinder_reviewed:
            self.cylinder_reviewed = True
            if len(self.cylinders) == 0:
                self.message_box(QMessageBox.Information, "Notice", "Please enter infomation of all gas sources for validation.")
            self.edit_cylinder()

    def cancel_process(self):
        msg = "Do you really want to abort validation process?"
        ret = self.message_box(QMessageBox.Question, "Stop Validation", msg, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            payload = {"username": self.current_user["username"], "action": "Abort H2O2 validation"}
            self.send_request("post", "action", payload)
            self.close()

    def data_analysis(self):
        # fake data used for testing
        # self.validation_results = dict(
        #     zero_air_nominal=0, zero_air_ch4_mean=-0.064, zero_air_ch4_sd=0.0685, zero_air_source="cylinder_#1_aaa",
        #     zero_air_ch4_diff=0.001, zero_air_h2o2_mean=0.001, zero_air_h2o_mean=0.001,
        #     calibrant1_nominal=2, calibrant1_ch4_mean=1.984, calibrant1_ch4_sd=0.0854, calibrant1_source="cylinder_#2_bbb",
        #     calibrant1_ch4_diff=0.001, calibrant1_h2o2_mean=0.001, calibrant1_h2o_mean=0.001,
        #     calibrant2_nominal=10, calibrant2_ch4_mean=10.025, calibrant2_ch4_sd=0.0719, calibrant2_source="cylinder_#3_ccc",
        #     calibrant2_ch4_diff=0.001, calibrant2_h2o2_mean=0.001, calibrant2_h2o_mean=0.001,
        #     calibrant3_nominal=100.2, calibrant3_ch4_mean=99.807, calibrant3_ch4_sd=0.1008, calibrant3_source="cylinder_#4_ddd",
        #     calibrant3_ch4_diff=0.001, calibrant3_h2o2_mean=0.001, calibrant3_h2o_mean=0.001
        # )

        # linear fitting
        self.step_names = ["zero_air", "calibrant1", "calibrant2"]
        if "calibrant3_ch4_mean" in self.validation_results:
            self.step_names.append("calibrant3")
            self.validation_results["calibrant3_step"] = "Calibrant 3"
        xdata = [self.validation_results[i + "_nominal"] for i in self.step_names]
        ydata = [self.validation_results[i + "_ch4_mean"] for i in self.step_names]
        coeffs = np.polyfit(xdata, ydata, 1)
        self.validation_results["ch4_slope"] = coeffs[0]
        self.validation_results["ch4_intercept"] = -coeffs[1]
        self.validation_results["h2o2_equivalent"] = -coeffs[1] / 70.0 * 1000.0
        yfit = np.poly1d(coeffs)(xdata)
        ybar = np.average(ydata)
        ssreg = np.sum((yfit - ybar)**2)
        sstot = np.sum((ydata - ybar)**2)
        self.validation_results["ch4_r2"] = ssreg / sstot
        # create image1: observed ch4 vs nominal ch4
        image1 = self.create_image(xdata, ydata, yfit, 'Surrogate Gas Validation', 'Nominal CH4 ppm', 'Observed CH4 ppm')

        # create image2: observed h2o2 vs nomial h2o2
        nominal_h2o2 = [self.validation_results[s + "_nominal"] / 70.0 * 1000.0 for s in self.step_names]
        observed_h2o2 = [self.validation_results[s + "_ch4_mean"] / 70.0 * 1000.0 for s in self.step_names]
        coeffs = np.polyfit(nominal_h2o2, observed_h2o2, 1)
        yfit2 = np.poly1d(coeffs)(nominal_h2o2)
        image2 = self.create_image(nominal_h2o2, observed_h2o2, yfit2, 'Surrogate Gas Validation', 'Nominal Equivalent H2O2 ppb',
                                   'Observed Equivalent H2O2 ppb')
        return [image1, image2]

    def create_image(self, xdata, ydata, yfitting, title, xlabel, ylabel):
        fig = plt.figure(figsize=(6, 5), facecolor=(1, 1, 1))
        ax = fig.gca()
        ax.plot(xdata, ydata, 'bo', xdata, yfitting, 'r-')
        ax.grid('on')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        max_x, min_x = max(xdata), min(xdata)
        offset = (max_x - min_x) * 0.05
        ax.set_xlim([min_x - offset, max_x + offset])
        ax.set_ylim([min_x - offset, max_x + offset])
        canvas = fig.canvas
        canvas.draw()
        size = canvas.size()
        width, height = size.width(), size.height()
        return QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)

    def create_report(self):
        imagelist = self.data_analysis()
        self.check_results()
        html = file(os.path.join(self.curr_dir, "ReportTemplate.html"), "r").read()
        # fill data in report
        items = ["step", "source", "info", "ch4_mean", "ch4_sd", "ch4_diff", "h2o2_mean", "h2o_mean"]
        for item in items:
            html = html.replace("{%s}" % ("more_"+item), \
                ("<td>{%s}</td>" % ("calibrant3_"+item)) \
                if "calibrant3_ch4_mean" in self.validation_results else "")
        html = html.replace("{analyzer_name}", os.uname()[1])
        start_time = time.localtime(self.current_user["login_time"])
        time_str = "%s (GMT%+d)" % (time.strftime("%Y-%m-%d %H:%M:%S", start_time), time.timezone / 36)
        html = html.replace("{start_time}", time_str)
        html = html.replace("{signature_time}", "%s (GMT%+d)" % (time.strftime("%Y-%m-%d %H:%M:%S"), time.timezone / 36))
        html = html.replace("{operator}", "%s %s (username: %s)" \
            % (self.current_user["first_name"] if self.current_user["first_name"] is not None else "",
            self.current_user["last_name"] if self.current_user["first_name"] is not None else "",
            self.current_user["username"]))
        html = html.replace("{signator}", "%s %s (username: %s)" \
            % (self.signature_user["first_name"] if self.signature_user["first_name"] is not None else "",
            self.signature_user["last_name"] if self.signature_user["first_name"] is not None else "",
            self.signature_user["username"]))
        for key in self.validation_results:
            html = html.replace("{%s}" % key, self.format_variable(key))
        self.report.setText(html)
        cursor = self.report.textCursor()
        doc = self.report.document()
        # insert images into document
        for idx in range(len(imagelist)):
            url = QUrl("mydata://report%d.png" % idx)
            doc.addResource(QTextDocument.ImageResource, url, QVariant(imagelist[idx]))
            image_format = QTextImageFormat()
            image_format.setName(url.toString())
            cursor.movePosition(QTextCursor.End)
            cursor.insertImage(image_format)

    def check_results(self):
        # check validation pass or fail
        self.report_status = {}
        if abs(self.validation_results["ch4_slope"] - 1) > 0.05:
            self.report_status["color_ch4_slope"] = 'red'
            self.validation_results["status_ch4_slope"] = "<font color='red'>Fail</font>"
        else:
            self.report_status["color_ch4_slope"] = 'green'
            self.validation_results["status_ch4_slope"] = "<font color='green'>Pass</font>"
        if self.validation_results["h2o2_equivalent"] > 10 or self.validation_results["h2o2_equivalent"] < -5:
            self.report_status["color_zero_h2o2"] = 'red'
            self.validation_results["status_zero_h2o2"] = "<font color='red'>Fail</font>"
        else:
            self.report_status["color_zero_h2o2"] = 'green'
            self.validation_results["status_zero_h2o2"] = "<font color='green'>Pass</font>"
        diffs = [self.validation_results[k] for k in self.validation_results \
            if k.endswith("_ch4_diff") and k.startswith("calibrant")]
        self.validation_results["max_ch4_deviation"] = max(diffs)
        if self.validation_results["max_ch4_deviation"] > 5:
            self.report_status["color_ch4_deviation"] = 'red'
            self.validation_results["status_ch4_deviation"] = "<font color='red'>Fail</font>"
        else:
            self.report_status["color_ch4_deviation"] = 'green'
            self.validation_results["status_ch4_deviation"] = "<font color='green'>Pass</font>"

    def create_summary(self, report_path):
        results = """
        <ul>
            <li><font color='{color_zero_h2o2}'>
                Zero H<sub>2</sub>O<sub>2</sub> = %.2f (Accepted range: [-5, 10])</font></li>
            <li><font color='{color_ch4_slope}'>
                CH<sub>4</sub> slope = %.6f (Accepted range: [0.95, 1.05])</font></li>
            <li><font color='{color_ch4_deviation}'>
                Max CH<sub>4</sub> deviation = %.2f (Accepted range: [0, 5])</font></li>
        </ul>
        """ % (self.validation_results["h2o2_equivalent"], self.validation_results["ch4_slope"],
               self.validation_results["max_ch4_deviation"])
        for k in self.report_status:
            results = results.replace("{%s}" % k, self.report_status[k])
        if "color='red'" in results:
            validation_pass = "fail"
            msg = "<h1><font color='red'>Validation Fail</font></h1>" + results + """
                <p>Please check system.</p>
                <p>Validation report created: %s</p>
            """ % report_path
            self.message_box(QMessageBox.Critical, "Validation Fail", msg)
        else:
            validation_pass = "pass"
            msg = "<h1><font color='green'>Validation Pass</font></h1>" + results \
                + "<p>Validation report created: %s</p>" % report_path
            self.message_box(QMessageBox.Information, "Validation Pass", msg)
        payload = {
            "username": self.signature_user["username"],
            "action": "Validation %s. Report created: %s" % (validation_pass, report_path)
        }
        self.send_request("post", "action", payload, use_token=True)

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
        printer = QPrinter(QPrinter.PrinterResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setPaperSize(QPrinter.B4)
        folder_name = time.strftime("%Y%m%d_%H%M%S")
        data_folder = os.path.join(self.report_dir, folder_name)
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        file_name = time.strftime("Validation_Report_%Y-%m-%d-%H-%M-%S.pdf")
        report_path = os.path.join(self.report_dir, folder_name, file_name)
        printer.setOutputFileName(report_path)
        doc = self.report.document()
        doc.setPageSize(QSizeF(printer.pageRect().size()))  #This is necessary if you want to hide the page number
        doc.print_(printer)
        # save data file
        with open(os.path.join(data_folder, "validation_data.csv"), "w") as f:
            f.write("Time, Step, " + ", ".join(self.data_fields) + "\n")
            for step in self.step_names:
                for idx in xrange(len(self.validation_data[step]['time'])):
                    f.write(str(self.validation_data[step]['time'][idx]))
                    f.write(", %s" % step)
                    for field in self.data_fields:
                        f.write(", %s" % (self.validation_data[step][field][idx]))
                    f.write("\n")
        self.create_summary(report_path)

    def download_report(self):
        cmd = self.config.get("Setup", "File_Manager_Cmd", "")
        cmd += " " + self.config.get("Setup", "File_Manager_Args", "")
        if len(cmd) > 0:
            from subprocess import Popen
            Popen(cmd.split())

    def exit_program(self):
        if self.message_box(QMessageBox.Question, "Question", "Do you really want to exit program?",
                            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
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
    for o, a in switches:
        options.setdefault(o, a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h', "")
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
    if "--no_login" in options:  # used for testing program without sqlite server
        no_login = True
    return (configFile, simulation, no_login)


if __name__ == "__main__":
    userAdminApp = SingleInstance("H2O2Validation")
    if not userAdminApp.alreadyrunning():
        app = QApplication(sys.argv)
        window = H2O2Validation(*handleCommandSwitches())
        window.show()
        app.exec_()
