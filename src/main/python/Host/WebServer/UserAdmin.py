import os
import sys
import time
import getopt
import requests
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from UserAdminFrame import UserAdminFrame

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

class MainWindow(UserAdminFrame):
    def __init__(self, configFile, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.host_session = requests.Session()
        self.role_list = []
        self.current_user = None    # user logged in
        self._get_system_variables()
    
    def _add_user(self):
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
        
    def _canel_add_user(self):
        self.add_user_widget.hide()
        self.user_admin_widget.show()
    
    def _cancel_login(self):
        self.input_user_name.clear()
        self.input_password.clear()
        
    def _change_user_pwd(self):
        # this function is called when admin is logged in 
        # and admin wants to change pwd of accounts
        self.input_new_password.clear()
        self.input_new_password2.clear()
        self.user_admin_widget.hide()
        self.new_user_info_widget.hide()
        self.label_curr_password.hide()
        self.input_curr_password.hide()
        self.add_user_widget.show()
    
    def _check_user_activity(self):
        # log off user if cursor doesn't move after certain amount of time
        pos = QCursor.pos()
        new_cursor_pos = [pos.x(), pos.y()]
        if cmp(new_cursor_pos, self.session_cursor_pos) != 0:
            self.session_cursor_pos = new_cursor_pos
            self.session_active_ts = time.time()
        elif time.time() - self.session_active_ts > self.session_lifetime:
            self.session_timer.stop()
            self.label_login_info.setText("Session time off.")
            self._user_log_off()
    
    def _change_user_role(self, role):
        query = "<p>Please confirm this action:</p><h2>Set %s as %s</h2>" % \
            (self.selected_user["username"], role)
        msg = QMessageBox(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel, self)
        if msg.exec_() == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], roles=role)
            self._send_request("post", "users", payload, use_token=True, show_error=True)
            self._update_user_list()
                
    def _check_user_input(self):
        new_user_input = self.new_user_info_widget.isVisible()
        password = str(self.input_new_password.text())
        errors = []
        # Here we only do preliminary checking. 
        # Further checking on user policies will be done on the server side
        if len(password) > 0:
            if password != self.input_new_password2.text():
                errors.append("Passwords not match.")
        else:
            errors.append("Password is blank.")
        if new_user_input:  # check user name
            new_username = str(self.input_new_user_name.text())
            if len(new_username) == 0:
                errors.append("UserName is blank.")
            elif new_username in self.all_users:
                errors.append("UserName already exists.")
        if len(errors) > 0:
            err ="<ul><li>%s</li></ul>" % ("</li><li>".join(errors))
            QMessageBox(QMessageBox.Critical, "Error", err, QMessageBox.Ok, self).exec_()
        else:   # go on to update/create user account
            if new_user_input:
                ret = self._save_new_user(new_username, password)
            else:
                ret = self._save_new_pwd(self.selected_user["username"], password)
            if ret is None:
                pass    # do nothing, give users a chance to edit their input
            elif "error" in ret:    # show errors and then let users edit input
                QMessageBox(QMessageBox.Critical, "Error", ret["error"], QMessageBox.Ok, self).exec_()
            else:   # succeed
                self.add_user_widget.hide()
                self.user_admin_widget.show()
    
    def _disable_policy_input(self, policy):
        check_control = getattr(self, "check_"+policy)
        input_control = getattr(self, "input_"+policy)
        enable = getattr(check_control, "isChecked")()
        self.config
        getattr(input_control, "setEnabled")(enable)
    
    def _disable_user(self):
        user_active = str(self.button_disable_user.text()) == "Enable User"
        query = "<p>Please confirm this action:</p><h2>%s %s</h2>" % \
            ("Enable" if user_active else "Disable", self.selected_user["username"])
        msg = QMessageBox(QMessageBox.Question, "Confirm Action", query, QMessageBox.Ok | QMessageBox.Cancel, self)
        if msg.exec_() == QMessageBox.Ok:
            payload = dict(command="update_user", username=self.selected_user["username"], active=int(user_active))
            self._send_request("post", "users", payload, use_token=True, show_error=True)
            self._update_user_list()
    
    def _display_user_info(self, user):
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
    
    def _get_history(self):
        actions = self._send_request("get", "action", {}, use_token=True)
        actions = ["%s %s: %s" % (a[0], a[1], a[2]) for a in actions]
        self.list_action_history.clear()
        self.list_action_history.addItems(actions)
    
    def _get_system_variables(self):
        self.config = self._send_request("get", "system", {'command':'get_all_variables'}, show_error=True)
        
        def set_policy_controls(policy):
            value = int(self.config[policy])
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
        self.check_password_mix_charset.setChecked(self.config["password_mix_charset"]=='True')

        self.session_lifetime = int(self.config["user_session_lifetime"]) * 60
    
    def _process_role_trigger(self, q):
        self._change_user_role(str(q.text()))
    
    def _revert_policy(self):
        pass
        
    def _save_new_pwd(self, username, password):
        payload = dict(command="update_user", username=username, password=password)
        ret = self._send_request("post", "users", payload, use_token=True)
        if "error" not in ret:
            msg = "Password is updated for %s!" % username
            b = QMessageBox(QMessageBox.Information, "New Password", msg, QMessageBox.Ok, self)
            b.exec_()
        return ret
        
    def _save_new_user(self, new_username, password):
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
        msg = QMessageBox(QMessageBox.Information, "New User Account", info, QMessageBox.Ok | QMessageBox.Cancel, self)
        ret = msg.exec_()
        if ret == QMessageBox.Ok:
            user.update(dict(password=password, command="create_user"))
            ret = self._send_request("post", "users", user, use_token=True)
            if "error" not in ret:
                self._update_user_list()
            return ret
        return None
    
    def _save_policy(self):
        def get_policy(policy):
            policy_check_control = getattr(self, "check_"+policy)
            policy_value_control = getattr(self, "input_"+policy)
            if getattr(policy_check_control, "isChecked")():
                self.config[policy] = str(getattr(policy_value_control, "value")())
            else:
                self.config[policy] = "-1"
        
        policies = ["password_length", "password_lifetime", "password_reuse_period", 
                    "user_login_attempts", "user_session_lifetime"]
        for p in policies:
            get_policy(p)    
        if self.check_password_mix_charset.isChecked():
            self.config["password_mix_charset"] = "True"
        else:
            self.config["password_mix_charset"] = "False"
        self._send_request("post", "system", self.config, use_token=True, show_error=True)
    
    def _select_user_from_table(self):
        indexes = self.table_user_list.selectionModel().selectedRows()
        if len(indexes) > 0:
            username = self.table_user_list.item(indexes[0].row(), 0)
            if username is not None:
                username = str(username.text())
                self.selected_user = self.all_users[username]
                self._display_user_info(self.selected_user)
                if self.selected_user["active"]:
                    self.button_disable_user.setText("Disable User")
                else:
                    self.button_disable_user.setText("Enable User")
                    
    def _send_request(self, action, api, payload, use_token=False, show_error=False):
        """
        action: 'get' or 'post'
        use_token: set to True if the api requires token for authentication
        show_error: if True, pop up a messagebox to display error messages
        """
        action_func = getattr(self.host_session, action)
        if use_token:
            header = {'Authentication': self.current_user["token"]}
        else:
            header = {}
        try:
            response = action_func(DB_SERVER_URL + api, data=payload, headers=header)
            return response.json()
        except Exception, err:
            if show_error:
                QMessageBox(QMessageBox.Critical, "Error", str(err), QMessageBox.Ok, self).exec_()
            return {"error": str(err)}
        
    def _update_user_list(self):
        payload = {'command': "get_all_users"}
        ret = self._send_request("get", "users", payload, use_token=True, show_error=True)
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
                    self._display_user_info(user)
            self.table_user_list.setSortingEnabled(True)        
    
    def _user_login(self):
        payload = {'command': "log_in_user",
                   'requester': "UserAdmin",
                   'username': str(self.input_user_name.text()), 
                   'password': str(self.input_password.text())}
        return_dict = self._send_request("post", "account", payload)
        if "error" not in return_dict:
            if "roles" in return_dict:
                if "Admin" in return_dict["roles"]:
                    self.input_user_name.clear()
                    self.input_password.clear()
                    self.current_user = return_dict
                    self._update_user_list()
                    self.home_widget.hide()
                    self.user_admin_widget.show()
                    # set up a timer for user session
                    self.session_timer = QTimer()
                    self.session_timer.timeout.connect(self._check_user_activity)
                    pos = QCursor.pos()
                    self.session_cursor_pos = [pos.x(), pos.y()]
                    self.session_active_ts = time.time()
                    self.session_timer.start(2000)
                else:
                    self.label_login_info.setText("Only Admin users can log in.")
                    self._send_request("post", "account", {"command":"log_out_user"})
        else:
            self.label_login_info.setText(return_dict["error"])
            
    def _user_log_off(self):
        self._send_request("post", "account", {"command":"log_out_user", 'requester': "UserAdmin"}, show_error=True)
        self.input_password.clear()
        self.input_user_name.clear()
        self.label_login_info.clear()
        self.input_user_name.setFocus()
        self.user_admin_widget.hide()
        self.home_widget.show()
        

HELP_STRING = """ModbusServer.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./ModbusServer.ini"
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
    configFile = "ModbusServer.ini"
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
    window.show()
    app.installEventFilter(window)
    app.exec_()