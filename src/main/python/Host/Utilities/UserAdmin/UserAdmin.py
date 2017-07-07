import os
import sys
import time
import getopt
import requests
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from UserAdminFrame import UserAdminFrame
from Host.Common.CustomConfigObj import CustomConfigObj

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
        self.input_password.clear()
        self.home_widget.show()
    
    def cancel_login(self):
        self.input_user_name.clear()
        self.input_password.clear()

    def change_password(self):
        # this function is called when password expires
        # and user is required to change pwd
        password = str(self.input_change_password.text())
        password2 = str(self.input_change_password2.text())
        if len(password) == 0:
            self.label_change_pwd_info.setText("New password cannot be blank!")
        elif password != password2:
            self.label_change_pwd_info.setText("Passwords not match!")
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
                self.cancel_change_pwd()
        self.input_change_password.clear()
        self.input_change_password2.clear()
        
    def change_user_pwd(self):
        # this function is called when admin is logged in 
        # and admin wants to change pwd of accounts
        self.input_new_password.clear()
        self.input_new_password2.clear()
        self.user_admin_widget.hide()
        self.new_user_info_widget.hide()
        self.label_curr_password.hide()
        self.input_curr_password.hide()
        self.add_user_widget.show()
        self.action = "change_pwd"

    def check_user_activity(self):
        # log off user if cursor doesn't move after certain amount of time
        pos = QCursor.pos()
        new_cursor_pos = [pos.x(), pos.y()]
        if cmp(new_cursor_pos, self.session_cursor_pos) != 0:
            self.session_cursor_pos = new_cursor_pos
            self.session_active_ts = time.time()
        elif time.time() - self.session_active_ts > self.session_lifetime:
            self.session_timer.stop()
            self.label_login_info.setText("Session time off.")
            self.user_log_off()
    
    def change_user_role(self, role):
        if self.selected_user["username"] == self.current_user["username"]:
            self.message_box(QMessageBox.Critical, "Error", "For safty reason, it is NOT allowed to change you own role!")
            return
        if role in self.selected_user["roles"]:
            return
        query = "<p>Please confirm this action:</p><h2>Set %s as %s</h2>" % \
            (self.selected_user["username"], role)
        msg = self.message_box(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel)
        if msg == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], roles=role)
            self.send_request("post", "users", payload, use_token=True, show_error=True)
            self.update_user_list()
                
    def check_user_input(self):
        password = str(self.input_new_password.text())
        errors = []
        # Here we only do preliminary checking. 
        # Further checking on user policies will be done on the server side
        if len(password) > 0:
            if password != self.input_new_password2.text():
                errors.append("Passwords not match.")
        else:
            errors.append("Password is blank.")
        if self.action == "add_user":  # check user name
            new_username = str(self.input_new_user_name.text())
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
        pattern = "<li><span style='font-weight: bold; color: rgb(0,202,255)'>%s</span> " + \
            "<span style='font-weight: bold; color: rgb(127,176,81)'>%s</span>: %s</li>"
        length = len(self.action_history)
        start = self.history_page*20
        if length/20 > self.history_page:
            end = start + 20
        else:
            end = length
            self.button_next_history.setEnabled(False)
        for idx in range(start, end):
            a = self.action_history[idx]
            list_actions += (pattern % (a[0], a[1], a[2]))
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
            self.message_box(QMessageBox.Critical, "Error", "Cannot disable yourselve!")
            return 
        query = "<p>Please confirm this action:</p><h2>%s %s</h2>" % \
            ("Enable" if user_active else "Disable", self.selected_user["username"])
        msg = self.message_box(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel)
        if msg == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], active=int(user_active))
            self.send_request("post", "users", payload, use_token=True, show_error=True)
            self.update_user_list()
    
    def display_user_info(self, user):
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
        """ % (user["username"], "True" if user["active"] else "False",
            user["first_name"], user["last_name"],
            user["employee_id"], user["phone_number"], ",".join(user["roles"]))
        self.label_user_info.setText(user_info)

    def get_role_list(self):
        payload = {'command': "get_roles"}
        ret = self.send_request("get", "users", payload, use_token=True, show_error=True)
        if "error" not in ret:
            set_current_roles = set(ret)
            set_old_roles = set(self.role_list)
            if set_old_roles - set_current_roles:
                # if some roles have been removed, we clear all actions in menu
                self.menu_user_role.clear()
                self.input_new_user_role.clear()
                set_old_roles = set()
            for role in set_current_roles-set_old_roles:
                self.menu_user_role.addAction(role)
                self.input_new_user_role.addItem(role)
            self.role_list = ret
    
    def get_history(self):
        self.action_history = self.send_request("get", "action", {}, use_token=True)
        self.action_history.reverse()
        self.history_page = 0
        if len(self.action_history) > 20:
            self.button_next_history.setEnabled(True)
        self.create_history_page()
    
    def get_system_variables(self):
        self.system_vars = self.send_request("get", "system", {'command':'get_all_variables'}, show_error=True)
        self.revert_policy()        
        self.session_lifetime = int(self.system_vars["user_session_lifetime"]) * 60

    def load_config(self):
        self.output_folder = self.config.get("Setup", "Output_Folder", ".")

    def message_box(self, icon, title, message, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(icon, title, message, buttons, self)
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
        fname = os.path.join(self.output_folder, time.strftime("%Y%m%d_%H%M%S.csv"))
        with open(fname, "w") as f:
            f.write("DateTime,UserName,Operation\n")
            for a in self.action_history:
                f.write("%s,%s,%s\n" % (a[0], a[1], a[2]))
        msg = "User history has been saved to %s." % fname
        self.message_box(QMessageBox.Information, "Save History", msg)
        
    def save_new_pwd(self, username, password):
        payload = dict(command="update_user", username=username, password=password)
        ret = self.send_request("post", "users", payload, use_token=True, show_error=True)
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
        """ % ("</li><li>".join([k+"="+user[k] for k in user]))
        ret = self.message_box(QMessageBox.Information, "New User Account", info, QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            user.update(dict(password=password, command="create_user"))
            ret = self.send_request("post", "users", user, use_token=True)
            if "error" not in ret:
                self.update_user_list()
            return ret
        return None
    
    def save_policy(self):
        def get_policy(policy):
            policy_check_control = getattr(self, "check_"+policy)
            policy_value_control = getattr(self, "input_"+policy)
            if getattr(policy_check_control, "isChecked")():
                self.system_vars[policy] = str(getattr(policy_value_control, "value")())
            else:
                self.system_vars[policy] = "-1"
        
        policies = ["password_length", "password_lifetime", "password_reuse_period", 
                    "user_login_attempts", "user_session_lifetime"]
        for p in policies:
            get_policy(p)    
        
        self.system_vars["password_mix_charset"] = "True" if self.check_password_mix_charset.isChecked() else "False"
        self.system_vars["save_history"] = "True" if self.check_save_history.isChecked() else "False"
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
                    self.display_user_info(user)
            self.table_user_list.setSortingEnabled(True)        
    
    def user_login(self):
        payload = {'command': "log_in_user",
                   'requester': "UserAdmin",
                   'username': str(self.input_user_name.text()), 
                   'password': str(self.input_password.text())}
        return_dict = self.send_request("post", "account", payload)
        if "error" not in return_dict:
            if "roles" in return_dict:
                if "Admin" in return_dict["roles"]:
                    self.input_user_name.clear()
                    self.input_password.clear()
                    self.current_user = return_dict
                    self.update_user_list()
                    self.get_role_list()
                    self.home_widget.hide()
                    self.user_admin_widget.show()
                    # set up a timer for user session
                    self.session_timer = QTimer()
                    self.session_timer.timeout.connect(self.check_user_activity)
                    pos = QCursor.pos()
                    self.session_cursor_pos = [pos.x(), pos.y()]
                    self.session_active_ts = time.time()
                    self.session_timer.start(2000)
                else:
                    self.label_login_info.setText("Only Admin users can log in.")
                    self.send_request("post", "account", {"command":"log_out_user"})
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
        else:
            self.label_login_info.setText(return_dict["error"])
            self.input_password.clear()
            
    def user_log_off(self):
        self.send_request("post", "account", {"command":"log_out_user", 'requester': "UserAdmin"}, show_error=True)
        self.input_password.clear()
        self.input_user_name.clear()
        self.label_login_info.clear()
        self.input_user_name.setFocus()
        self.user_admin_widget.hide()
        self.add_user_widget.hide()
        self.change_password_widget.hide()
        self.home_widget.show()
        

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
    app = QApplication(sys.argv)
    window = MainWindow(*handleCommandSwitches())
    #window.setWindowState(Qt.WindowFullScreen)
    window.get_system_variables()
    window.show()
    app.installEventFilter(window)
    app.exec_()