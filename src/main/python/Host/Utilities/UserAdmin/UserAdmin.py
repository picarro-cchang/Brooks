import os
import sys
import time
import getopt
import requests
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from UserAdminFrame import UserAdminFrame
from Host.Common.timestamp import timestampToLocalDatetime
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.SingleInstance import SingleInstance

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

class MainWindow(UserAdminFrame):
    def __init__(self, configFile, parent=None):
        super(MainWindow, self).__init__(parent)
        if not os.path.exists(configFile):
            raise Exception("Configuration file not found: %s" % configFile)
        self.config = CustomConfigObj(configFile)
        self.load_config()
        self.host_session = requests.Session()
        self.role_list = []
        self.action_history = []
        self.current_tab = 0
        self.current_user = None    # user logged in
    
    def add_user(self):
        self.input_new_user_name.clear()
        self.input_new_employee_id.clear()
        self.input_new_first_name.clear()
        self.input_new_last_name.clear()
        self.input_new_password.clear()
        self.input_new_password2.clear()
        self.input_new_phone_num.clear()
        self.input_new_phone_ext.clear()
        self.user_admin_widget.hide()
        # hide current password field
        self.label_curr_password.hide()
        self.input_curr_password.hide()
        self.new_user_info_widget.show()
        self.add_user_widget.show()
        self.action = "add_user"
        
    def cancel_add_user(self):
        self.add_user_widget.hide()
        self.user_admin_widget.show()

    def cancel_change_pwd(self):
        self.change_password_widget.hide()
        if self.action == "change_pwd_after_login":
            self.user_admin_widget.show()
        else:
            self.input_password.clear()
            self.home_widget.show()
    
    def cancel_login(self):
        self.close()

    def change_password(self):
        # this function is called when user needs to change his own pwd
        password = str(self.input_change_password.text())
        password2 = str(self.input_change_password2.text())
        if len(password) == 0:
            self.label_change_pwd_info.setText("New password cannot be blank!")
        elif password != password2:
            self.label_change_pwd_info.setText("Passwords do not match!")
        else:
            payload = {"command": "change_password",
                       "requester": "UserAdmin",
                       "password": self.current_user["password"],
                       "username": self.current_user["username"],
                       "new_password": password}
            return_dict = self.send_request("post", "account", payload)
            if "error" in return_dict:
                self.label_change_pwd_info.setText(return_dict["error"])
            else:
                msg = "Password of account %s has been changed" % self.current_user["username"]
                self.message_box(QMessageBox.Information, "Change Password", msg)
                self.action = ""
                self.cancel_change_pwd()
        self.input_change_password.clear()
        self.input_change_password2.clear()
        
    def change_user_pwd(self):
        # this function is called when admin is logged in 
        # and admin wants to change pwd of accounts
        if self.selected_user["username"] == self.current_user["username"]:
            self.home_widget.hide()
            self.user_admin_widget.hide()
            self.input_change_password.clear()
            self.input_change_password2.clear()
            self.label_change_pwd_info.clear()
            self.change_password_widget.show()
            self.input_change_password.setFocus()
            self.action = "change_pwd_after_login"
        else:
            self.input_new_password.clear()
            self.input_new_password2.clear()
            self.user_admin_widget.hide()
            self.new_user_info_widget.hide()
            self.label_curr_password.hide()
            self.input_curr_password.hide()
            self.add_user_widget.show()
            self.action = "change_pwd"

    def change_user_role(self, role):
        if self.selected_user["username"] == self.current_user["username"]:
            self.message_box(QMessageBox.Critical, "Error", "For safety reason, it is NOT allowed to change your own role!")
            return
        if role in self.selected_user["roles"]:
            return
        query = "<p>Please confirm this action:</p><h2>Set %s as %s</h2>" % \
            (self.replace_html_special_chars(self.selected_user["username"]), role)
        msg = self.message_box(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel)
        if msg == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], roles=role)
            self.send_request("post", "users", payload, use_token=True, show_error=True)
            self.update_user_list()

    def check_user_activity(self):
        # log off user if cursor doesn't move after certain amount of time
        if self.session_lifetime >= 0:
            pos = QCursor.pos()
            new_cursor_pos = [pos.x(), pos.y()]
            if cmp(new_cursor_pos, self.session_cursor_pos) != 0:
                self.session_cursor_pos = new_cursor_pos
                self.session_active_ts = time.time()
            elif time.time() - self.session_active_ts > self.session_lifetime:
                self.user_log_off()
                
    def check_user_input(self):
        password = str(self.input_new_password.text())
        errors = []
        # Here we only do preliminary checking. 
        # Further checking on user policies will be done on the server side
        if len(password) > 0:
            if password != self.input_new_password2.text():
                errors.append("Passwords do not match.")
        else:
            errors.append("Password is blank.")
        if self.action == "add_user":  # check user name
            new_username = str(self.input_new_user_name.text()).strip()
            if len(new_username) == 0:
                errors.append("UserName is blank.")
            elif new_username in self.all_users:
                errors.append("UserName already exists.")
        if len(errors) > 0:
            err ="<ul><li>%s</li></ul>" % ("</li><li>".join(errors))
            self.message_box(QMessageBox.Critical, "Error", err)
        else:   # go on to update/create user account
            if self.action == "add_user":
                ret = self.save_new_user(new_username, password)
            else:
                ret = self.save_new_pwd(self.selected_user["username"], password)
            if ret is None:
                pass    # do nothing, give users a chance to edit their input
            elif "error" in ret:    # show errors and then let users edit input
                self.message_box(QMessageBox.Critical, "Error", ret["error"])
            else:   # succeed
                self.add_user_widget.hide()
                self.user_admin_widget.show()

    def create_history_page(self):
        list_actions = ""
        pattern = "<li><span style='font-weight: bold; color: rgb(0,202,255);'>%s</span> " + \
            "<span style='font-weight: bold; color: rgb(127,176,81);'>%s</span>: %s</li>"
        length = len(self.action_history)
        start = self.history_page*20
        if length/20 > self.history_page:
            end = start + 20
        else:
            end = length
            self.button_next_history.setEnabled(False)
        for idx in range(start, end):
            a = self.action_history[idx]
            list_actions += (pattern % (
                timestampToLocalDatetime(a[0]).strftime("%Y-%m-%d %H:%M:%S"), 
                self.replace_html_special_chars(a[1]), 
                self.replace_html_special_chars(a[2])))
        self.label_action_history.setText("<ul>%s</ul>" % list_actions)
    
    def disable_policy_input(self, policy):
        check_control = getattr(self, "check_"+policy)
        input_control = getattr(self, "input_"+policy)
        enable = getattr(check_control, "isChecked")()
        getattr(input_control, "setEnabled")(enable)
    
    def disable_user(self):
        user_active = str(self.button_disable_user.text()) == "Enable User"
        # prevent user disabling himself
        if self.selected_user["username"] == self.current_user["username"] and (not user_active):
            self.message_box(QMessageBox.Critical, "Error", "Cannot disable yourself!")
            return 
        query = "<p>Please confirm this action:</p><h2>%s %s</h2>" % \
            ("Enable" if user_active else "Disable", 
            self.replace_html_special_chars(self.selected_user["username"]))
        msg = self.message_box(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel)
        if msg == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], active=int(user_active))
            self.send_request("post", "users", payload, use_token=True, show_error=True)
            self.update_user_list()
    
    def display_user_info(self, user):
        username = self.replace_html_special_chars(user["username"])
        last_name = self.replace_html_special_chars(user["last_name"])
        first_name = self.replace_html_special_chars(user["first_name"])
        user_info = """
            <html>
                <head>
                    <style>
                        td {padding-right:10px}
                        .attr {font-weight:600;}
                    </style>
                </head>
                <body>
                    <table>
                        <tr><td class='attr'>UserName</td><td>%s</td><td class='attr'>Active<td>%s</td></tr>
                        <tr><td class='attr'>Name</td><td>%s %s</td><td class='attr'>Employee ID</td><td>%s</td></tr>
                        <tr><td class='attr'>Phone</td><td>%s</td><td class='attr'>Roles</td><td>%s</td></tr>
                    </table>
                </body>
            </html>
        """ % (username, "True" if user["active"] else "False", first_name, last_name,
            user["employee_id"], user["phone_number"], ",".join(user["roles"]))
        self.label_user_info.setText(user_info)

    def download_history(self):
        self.save_history()
        if self.file_manager_cmd:
            from subprocess import Popen
            cmd = self.file_manager_cmd + " " + self.file_manager_args
            Popen(cmd.split())

    def get_role_list(self):
        payload = {'command': "get_roles"}
        ret = self.send_request("get", "users", payload, use_token=True, show_error=True)
        if "error" not in ret:
            self.role_list = ret  
            self.input_new_user_role.clear()  
            for role in ret:
                self.input_new_user_role.addItem(role)      
    
    def get_history(self):
        self.action_history = self.send_request("get", "action", {}, use_token=True)
        self.action_history.reverse()
        self.history_page = 0
        if len(self.action_history) > 20:
            self.button_next_history.setEnabled(True)
        self.create_history_page()

    def get_policies(self, checking=False):
        def get_policy(policy):
            policy_check_control = getattr(self, "check_"+policy)
            try:
                policy_value_control = getattr(self, "input_"+policy)
            except:
                policy_value_control = None
            if policy_value_control:
                if getattr(policy_check_control, "isChecked")():
                    value = str(getattr(policy_value_control, "value")())
                else:
                    value = "-1"
            else:
                value = "True" if getattr(policy_check_control, "isChecked")() else "False"
            if checking:
                return self.system_vars[policy] == value
            else:
                self.system_vars[policy] = value
        
        policies = ["password_length", "password_lifetime", "password_reuse_period", 
                    "user_login_attempts", "user_session_lifetime", "password_mix_charset",
                    "save_history"]
        for p in policies:
            if checking and (not get_policy(p)):
                return False
            else:
                get_policy(p)
        return True
    
    def get_system_variables(self):
        self.system_vars = self.send_request("get", "system", {'command':'get_all_variables'}, show_error=True)
        self.revert_policy()        
        self.session_lifetime = int(self.system_vars["user_session_lifetime"]) * 60

    def load_config(self):
        self.output_folder = self.config.get("Setup", "Output_Folder", ".")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.file_manager_cmd = self.config.get("Setup", "File_Manager_Cmd", "")
        self.file_manager_args = self.config.get("Setup", "File_Manager_Args", "")

    def message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(icon, title, message, buttons, self)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.FramelessWindowHint | Qt.ApplicationModal)
        return msg_box.exec_()

    def next_history_page(self):
        self.history_page += 1
        self.button_prev_history.setEnabled(True)
        self.create_history_page()

    def prev_history_page(self):
        self.history_page -= 1
        self.button_next_history.setEnabled(True)
        if self.history_page == 0:
            self.button_prev_history.setEnabled(False)
        self.create_history_page()
    
    def process_role_trigger(self, q):
        self.change_user_role(str(q.text()))

    def replace_html_special_chars(self, string):
        string = string.replace("&", "&amp;")
        string = string.replace("<", "&lt;")
        string = string.replace(">", "&gt;")
        return string
    
    def revert_policy(self):
        def set_policy_controls(policy):
            value = int(self.system_vars[policy])
            enable = (value >= 0)
            policy_check_control = getattr(self, "check_"+policy)
            policy_value_control = getattr(self, "input_"+policy)
            getattr(policy_check_control, "setChecked")(enable)
            getattr(policy_value_control, "setEnabled")(enable)
            if enable:
                getattr(policy_value_control, "setValue")(value)
                            
        policies = ["password_length", "password_lifetime", "password_reuse_period", 
                    "user_login_attempts", "user_session_lifetime"]
        for p in policies:
            set_policy_controls(p)
        self.check_password_mix_charset.setChecked(self.system_vars["password_mix_charset"]=='True')
        self.check_save_history.setChecked(self.system_vars["save_history"]=='True')

    def save_history(self):
        # TO DO: export history in pdf format
        if len(self.action_history) == 0:
            msg = "User history is empty. Please click Refresh button to download history from server"
            self.message_box(QMessageBox.Critical, "Error", msg)
            return 1
        fname = os.path.join(self.output_folder, "UserHistory.csv")
        with open(fname, "w") as f:
            f.write("DateTime,UserName,Operation\n")
            for a in self.action_history:
                f.write("%s,%s,%s\n" % (a[0], a[1], a[2]))
        msg = "User history has been saved in %s." % fname
        self.message_box(QMessageBox.Information, "Save History", msg)
        
    def save_new_pwd(self, username, password):
        payload = dict(command="update_user", username=username, password=password)
        ret = self.send_request("post", "users", payload, use_token=True)
        if "error" not in ret:
            msg = "Password is updated for %s!" % username
            self.message_box(QMessageBox.Information, "New Password", msg)
        return ret
        
    def save_new_user(self, new_username, password):
        phone = str(self.input_new_phone_num.text())
        ext = str(self.input_new_phone_ext.text())
        phone += (","+ext) if len(ext) > 0 else ""
        user = dict(username=str(new_username),
                    last_name=str(self.input_new_last_name.text()),
                    first_name=str(self.input_new_first_name.text()),
                    employee_id=str(self.input_new_employee_id.text()),
                    phone_number=phone,
                    roles=str(self.input_new_user_role.currentText()))
        info ="""
            <h2>Please verify user information carefully.</h2>
            <p>User account can NOT be deleted, and many fields can NOT be modified after user account is created.</p>
            <p><ul><li>%s</li></ul></p>
        """ % ("</li><li>".join([k+"="+self.replace_html_special_chars(user[k]) for k in user]))
        ret = self.message_box(QMessageBox.Information, "New User Account", info, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            user.update(dict(password=password, command="create_user"))
            ret = self.send_request("post", "users", user, use_token=True)
            if "error" not in ret:
                self.update_user_list()
            return ret
        return None
    
    def save_policy(self):
        self.get_policies()
        ret = self.send_request("post", "system", self.system_vars, use_token=True, show_error=True)
        if "error" not in ret:
            self.message_box(QMessageBox.Information, "Save", "User policies have been updated!")
            self.session_lifetime = int(self.system_vars["user_session_lifetime"]) * 60
    
    def select_user_from_table(self):
        indexes = self.table_user_list.selectionModel().selectedRows()
        if len(indexes) > 0:
            username = self.table_user_list.item(indexes[0].row(), 0)
            if username is not None:
                username = str(username.text())
                self.selected_user = self.all_users[username]
                self.display_user_info(self.selected_user)
                if self.selected_user["active"]:
                    self.button_disable_user.setText("Disable User")
                else:
                    self.button_disable_user.setText("Enable User")
                self.setup_role_menu(self.selected_user["roles"])
                    
    def send_request(self, action, api, payload, use_token=False, show_error=False):
        """
        action: 'get' or 'post'
        use_token: set to True if the api requires token for authentication
        show_error: if True, pop up a messagebox to display error messages
        """
        if use_token:
            header = {'Authentication': self.current_user["token"]}
        else:
            header = {}
        response = self._send_request(action, api, payload, header)
        if "error" in response and show_error:
            self.message_box(QMessageBox.Critical, "Error", response["error"])
        return response

    def _send_request(self, action, api, payload, header):
        action_func = getattr(self.host_session, action)
        try:
            response = action_func(DB_SERVER_URL + api, data=payload, headers=header)
            return response.json()
        except Exception, err:
            return {"error": str(err)}

    def setup_role_menu(self, roles):
        set_all_roles = set(self.role_list)        
        # clear all actions in menu
        self.menu_user_role.clear()
        for role in set_all_roles-set(roles):
            self.menu_user_role.addAction(role)            

    def switch_tab(self, tabindex):
        if self.user_admin_tabs.tabText(self.current_tab) == "User Policies":
            if not self.get_policies(checking=True):
                msg = "Do you want to save your changes in user policies?"
                ret = self.message_box(QMessageBox.Question, "Save Policies?", msg, QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    self.save_policy()
                else:
                    self.revert_policy()
        if self.user_admin_tabs.tabText(tabindex) == "User History":
            self.get_history()
        self.current_tab = tabindex
        
    def update_user_list(self):
        payload = {'command': "get_all_users"}
        ret = self.send_request("get", "users", payload, use_token=True, show_error=True)
        if "error" not in ret:
            self.all_users = {user["username"]: user for user in ret}
            self.table_user_list.setSortingEnabled(False)
            num_users = len(ret)
            num_rows = self.table_user_list.rowCount()
            if num_users > num_rows:
                for _ in range(num_users-num_rows):
                    self.table_user_list.insertRow(0)
            for idx, user in enumerate(ret):
                self.table_user_list.setItem(idx,0, QTableWidgetItem(user["username"]))
                self.table_user_list.setItem(idx,1, QTableWidgetItem(user["last_name"]))
                self.table_user_list.setItem(idx,2, QTableWidgetItem(user["first_name"]))
                self.table_user_list.setItem(idx,3, QTableWidgetItem(",".join(user["roles"])))
                if idx == 0:
                    self.table_user_list.selectRow(0)
                    self.select_user_from_table()
            self.table_user_list.setSortingEnabled(True)        
    
    def user_login(self):
        password = str(self.input_password.text())
        payload = {'command': "log_in_user",
                   'requester': "UserAdmin",
                   'username': str(self.input_user_name.text()), 
                   'password': password}
        return_dict = self.send_request("post", "account", payload)
        if "error" not in return_dict:
            if "roles" in return_dict and "Admin" in return_dict["roles"]:
                self.input_user_name.clear()
                self.input_password.clear()
                self.current_user = return_dict
                self.current_user["password"] = password
                self.get_role_list()
                self.update_user_list()
                self.home_widget.hide()
                self.user_admin_widget.show()
                self.get_system_variables()
                # set up a timer for user session
                self.session_timer = QTimer()
                self.session_timer.timeout.connect(self.check_user_activity)
                pos = QCursor.pos()
                self.session_cursor_pos = [pos.x(), pos.y()]
                self.session_active_ts = time.time()
                self.session_timer.start(2000)
        elif "Password expire" in return_dict["error"]:
            self.current_user = dict(
                username=str(self.input_user_name.text()),
                password=str(self.input_password.text())
                )
            self.home_widget.hide()
            self.input_change_password.clear()
            self.input_change_password2.clear()
            self.change_password_widget.show()
            self.label_change_pwd_info.setText("Password expires! Please change your password.")
            self.action = "change_expired_pwd"
        else:
            if "HTTPConnection" in return_dict["error"]:
                msg = "Unable to connect database server!"
            else:
                msg = return_dict["error"]
            self.label_login_info.setText(msg)
            self.input_password.clear()
            
    def user_log_off(self):
        self.send_request("post", "account", {"command":"log_out_user", 'requester': "UserAdmin"}, show_error=True)
        self.session_timer.stop()
        self.close()        
        # self.input_password.clear()
        # self.input_user_name.clear()
        # self.label_login_info.clear()
        # self.input_user_name.setFocus()
        # self.user_admin_widget.hide()
        # self.add_user_widget.hide()
        # self.change_password_widget.hide()
        # self.home_widget.show()
        

HELP_STRING = """UserAdmin.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "UserAdmin.ini"
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
    configFile = "UserAdmin.ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    return (configFile,)

if __name__ == "__main__":
    userAdminApp = SingleInstance("PicarroUserAdmin")
    if not userAdminApp.alreadyrunning():
        app = QApplication(sys.argv)
        window = MainWindow(*handleCommandSwitches())
        #window.setWindowState(Qt.WindowFullScreen)
        window.show()
        app.installEventFilter(window)
        app.exec_()
