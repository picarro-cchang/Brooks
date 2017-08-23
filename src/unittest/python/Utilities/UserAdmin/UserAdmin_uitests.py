import os
import sys
import unittest
from datetime import datetime
from mockito import patch, unstub
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QApplication, QMessageBox
from Host.Utilities.UserAdmin.UserAdmin import MainWindow
from Host.WebServer.SQLiteServer import SQLiteServer
from Host.WebServer.SQLiteServer import app as flask_app

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "UserAdmin.ini")
app = QApplication(sys.argv)

class TestUserAdmin(unittest.TestCase):
    def setUp(self):
        self.request_context = flask_app.test_request_context()
        self.request_context.push()
        self.server = SQLiteServer(dummy=True)
        self.interface = MainWindow(CONFIG_FILE)  
        self.message_box_content = {"title":"", "msg":"", "response":QMessageBox.Ok}
        patch(self.interface.message_box, self.message_box)
        patch(self.interface._send_request, self.server.get_request)

    def tearDown(self):
        self.request_context.pop()
        self.interface.close()
        self.interface = None
        unstub()

    def message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        self.message_box_content["title"] = title
        self.message_box_content["msg"] = message
        return self.message_box_content["response"]

    def login_user(self, username, password):
        self.interface.input_user_name.setText(username)
        self.interface.input_password.setText(password)
        QTest.mouseClick(self.interface.button_user_login, Qt.LeftButton)

    def test_add_user(self):
        # login
        self.login_user("admin", "admin")
        self.assertTrue(self.interface.current_user["username"] == "admin")
        self.assertTrue(self.interface.table_user_list.rowCount() == 3) # 3 default users 
        # enter user creation interface
        QTest.mouseClick(self.interface.button_add_user, Qt.LeftButton)
        # test1: only enter username
        self.interface.input_new_user_name.setText("yren")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue("Password is blank" in self.message_box_content["msg"])
        # test2: passwords not match
        self.interface.input_new_password.setText("123")
        self.interface.input_new_password2.setText("12345")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue("Passwords do not match" in self.message_box_content["msg"])
        # test3: password too short
        self.interface.input_new_password.setText("12345")
        self.interface.input_new_password2.setText("12345")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue("Password is too short" in self.message_box_content["msg"])
        # test4: correct input
        self.interface.input_new_password.setText("123456")
        self.interface.input_new_password2.setText("123456")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue(self.interface.table_user_list.rowCount() == 4) # 4 users now
        self.assertTrue("yren" in self.interface.all_users)

    def test_disable_user(self):
        # login
        self.login_user("admin", "admin")
        # disable tech
        self.interface.table_user_list.selectRow(0)
        self.interface.select_user_from_table()
        username = self.interface.selected_user["username"]
        self.assertTrue(self.interface.all_users[username]["active"])
        QTest.mouseClick(self.interface.button_disable_user, Qt.LeftButton)
        self.assertFalse(self.interface.all_users[username]["active"])
        # enable tech
        self.interface.table_user_list.selectRow(0)
        self.interface.select_user_from_table()
        QTest.mouseClick(self.interface.button_disable_user, Qt.LeftButton)
        self.assertTrue(self.interface.all_users[username]["active"])

    def test_change_pwd_by_admin(self):
        # login
        self.login_user("admin", "admin")
        # change pwd of tech
        self.interface.table_user_list.selectRow(0)
        self.interface.select_user_from_table()
        username = self.interface.selected_user["username"]
        QTest.mouseClick(self.interface.button_change_pwd, Qt.LeftButton)
        # test1: password too short
        self.interface.input_new_password.setText("12345")
        self.interface.input_new_password2.setText("12345")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue("Password is too short" in self.message_box_content["msg"])
        # test2: correct input
        self.interface.input_new_password.setText("Extreme_Science")
        self.interface.input_new_password2.setText("Extreme_Science")
        QTest.mouseClick(self.interface.button_add_user_next, Qt.LeftButton)
        self.assertTrue("Password is updated" in self.message_box_content["msg"])
        self.assertTrue(("change %s password" % username) in self.server.ds.action_model[-1].action)

    def test_change_own_password(self):
        self.login_user("admin", "admin")
        # admin should already be selected after login
        QTest.mouseClick(self.interface.button_change_pwd, Qt.LeftButton) 
        # click next without new pwd 
        QTest.mouseClick(self.interface.button_change_user_pwd, Qt.LeftButton)
        self.assertTrue("New password cannot be blank" in self.interface.label_change_pwd_info.text()) 
        # try again with new pwd
        self.interface.input_change_password.setText("123456")
        self.interface.input_change_password2.setText("123456")
        QTest.mouseClick(self.interface.button_change_user_pwd, Qt.LeftButton)
        self.assertTrue("has been changed" in self.message_box_content["msg"])
        self.login_user("admin", "12345")
        self.assertTrue("admin" in self.server.ds.action_model[-1].username) 
        self.assertTrue("log in" in self.server.ds.action_model[-1].action)        

    def test_password_expire(self):
        self.server.ds.save_user_password("admin", "admin", created_time=datetime(1969,7,20,20,18,0,0))
        self.login_user("admin", "admin")
        self.assertTrue("Password expires" in self.interface.label_change_pwd_info.text())
        self.interface.input_change_password.setText("Extreme_Science")
        self.interface.input_change_password2.setText("Extreme_Science")
        QTest.mouseClick(self.interface.button_change_user_pwd, Qt.LeftButton)
        self.assertTrue("change password" in self.server.ds.action_model[-1].action)
        # try to log in using old pwd
        self.login_user("admin", "admin")
        self.assertTrue("Username and password do not match" in self.interface.label_login_info.text())
        # login using the new pwd
        self.login_user("admin", "Extreme_Science")
        self.assertTrue(self.interface.table_user_list.rowCount() == 3) # user list is populated after login

    def test_change_system_variable(self):
        self.login_user("admin", "admin")
        self.interface.input_password_lifetime.setValue(1)
        # revert policy
        QTest.mouseClick(self.interface.button_user_revert_policy, Qt.LeftButton)
        self.assertTrue(self.interface.input_password_lifetime.value() == 183)
        # change policy and save
        self.interface.input_password_lifetime.setValue(1)
        QTest.mouseClick(self.interface.button_user_save_policy, Qt.LeftButton)
        self.assertTrue("User policies have been updated" in self.message_box_content["msg"])
        p_pwd_lifetime = None
        for p in self.server.ds.system_model:
            if p.name=='password_lifetime':
                p_pwd_lifetime = p
                break
        self.assertTrue(p_pwd_lifetime.value == "1")
    
if __name__ == '__main__':
    if is_running_under_teamcity():
        runner = TeamcityTestRunner()
    else:
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
