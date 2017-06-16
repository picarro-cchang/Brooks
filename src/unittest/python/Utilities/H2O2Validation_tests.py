import os
import sys
import time
import unittest
from mockito import patch, unstub
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication
from Host.Utilities.H2O2ValidationWizard.H2O2Validation import H2O2Validation, validation_steps
from Host.Utilities.BuildHelper.BuildHelper import isAnalyzerToBuild

CONFIG_FILE = os.path.abspath(r"./H2O2Validation.ini")

app = QApplication(sys.argv)

@unittest.skipUnless(isAnalyzerToBuild(["NCDS"]), "Analyzer type not match")
class TestH2O2Validation(unittest.TestCase):
    def setUp(self):
        self.wizard = H2O2Validation(CONFIG_FILE, simulation=True, no_login=False, unit_test=True)              

    def tearDown(self):
        self.wizard.close()
        self.wizard = None

    def bypass_login_screen(self):
        self.wizard.login_frame.hide()
        self.wizard.top_frame.show()
        self.wizard.wizard_frame.show()
        self.wizard.start_data_collection()

    def dummy_server(self, action, api, payload):
        if api == "account" and action == "post":
            if payload["command"] == "log_in_user" and "requester" in payload:
                for user in self.database["User"]:
                    if user["username"] == payload["username"]:
                        if user["password"] == payload["password"]:
                            return user
                        else: return {"error": "Password not match!"}
                return {"error": "Username not found!"}
        elif api == "action" and action == "post":
            self.database["UserAction"].append("%s %s" % (payload["username"], payload["action"]))
            return {"status": "succeed"}
        raise Exception("Error in SQLite server call: action=%s, api=%s, payload=%s" % (action, api, payload))

    def setup_server(self):
        patch(self.wizard.send_request, self.dummy_server)
        self.database = {
            "UserAction": [],
            "User": [{"username":"admin","password":"admin","roles":["Admin"],"first_name":"","last_name":""}]
            }

    def test_full_process(self):
        self.setup_server()
        # login
        self.wizard.input_user_name.setText("admin")
        self.wizard.input_password.setText("admin")
        QTest.mouseClick(self.wizard.button_user_login, Qt.LeftButton)
        QTest.qWait(30)
        self.assertTrue(self.wizard.current_user["username"] == "admin")
        self.assertTrue("Admin" in self.wizard.current_user["roles"])
        # validation
        next_button = self.wizard.button_next_step
        measurements = ["zero_air", "calibrant1", "calibrant2", "calibrant3"]
        nominal_concentraion = [0, 2, 10, 100]
        for step in range(4):
            stage = measurements[step]
            QTest.mouseClick(next_button, Qt.LeftButton)
            if step > 0:    # enter nominal concentraion of calibrant
                self.wizard.input_nominal_concentration.setText(str(nominal_concentraion[step]))
            QTest.mouseClick(next_button, Qt.LeftButton)
            self.wizard.message_box_content["title"] = ""
            self.assertTrue(validation_steps[self.wizard.current_step] == stage)
            QTest.qWait(1500)   # data collection
            self.assertTrue(stage + "_mean" in self.wizard.validation_results)
            self.assertTrue(self.wizard.message_box_content["title"] == "Measurement Done")
        # create report
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(30)
        self.assertTrue(self.wizard.validation_results["ch4_r2"] > 0.9)
        # save report
        QTest.mouseClick(self.wizard.button_save_report, Qt.LeftButton)
        QTest.qWait(200)
        self.assertTrue("Create validation report" in self.database["UserAction"][-1])
        filename = self.database["UserAction"][-1].split(":")[1]
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(curr_dir, filename.strip())
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)
        # clear mockito functions
        unstub()

    def test_low_cavity_pressure(self):
        self.wizard.simulation_dict["CavityPressure"] = "100-x"
        self.bypass_login_screen()
        next_button = self.wizard.button_next_step
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(1000)   # zero-air measurement
        self.assertTrue("Cavity pressure is out of range" in self.wizard.message_box_content["msg"])

    def test_wrong_nomial_concentration(self):
        self.bypass_login_screen()
        for s in validation_steps:
            if validation_steps[s] == "calibrant1":
                self.wizard.current_step = s - 2
                break
        next_button = self.wizard.button_next_step
        QTest.mouseClick(next_button, Qt.LeftButton)
        self.wizard.input_nominal_concentration.setText("wrong concentration")
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(30)
        self.assertTrue(self.wizard.message_box_content["title"] == "Error")
        # simulated concentration is 2; intentionally enter a wrong number
        self.wizard.input_nominal_concentration.setText("10")
        QTest.mouseClick(next_button, Qt.LeftButton)
        QTest.qWait(1500)   # data collection
        self.assertTrue("Measurement result is too far away" in self.wizard.message_box_content["msg"])

if __name__ == '__main__':
    unittest.main()