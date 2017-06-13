import os
import sys
import time
import getopt
import requests

from PyQt4.QtCore import *
from PyQt4.QtGui import *

DB_SERVER_URL = "http://127.0.0.1:3600/api/v1.0/"

class MainWindow(QMainWindow):
    def __init__(self, configFile, parent=None):
        super(MainWindow, self).__init__(parent)
        
        #Set Picarro marketing colors to be used for manual color changes
        picarroGreen = QColor(108,179,63).rgba()
        picarroGrey = QColor(64,64,64,).rgba()
        picarroBlack = QColor(0,0,0).rgba()

        # Set-up Drop Shadow effect to be used on elements
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setColor(QColor(30,30,30,180))
        self.shadow.setBlurRadius(5)
                
        self.create_widgets()
        self.setWindowTitle("User Management")
        self.resize(800,600)
        
        self.host_session = requests.Session()
        self.role_list = []
        self.current_user = None    # user logged in
        self._get_system_variables()
        
    def create_widgets(self):
        def spin_box(value=0, min=0, max=100, step=1):
            sBox = QSpinBox()
            sBox.setMinimum(min)
            sBox.setMaximum(max)
            sBox.setSingleStep(step)
            sBox.setProperty("value", value)
            return sBox
            
        def control_box(caption, control, caption_on_left=False):
            box = QFormLayout()
            if caption_on_left:
                box.addRow(caption, control)
            else:
                box.addRow(control, QLabel(caption))
            return box
    
        # Most buttons are placed in QFormLayouts as it is a convenient class
        # for lining up buttons and text fields.
        # The buttons are organized in groups and a group of buttons is put
        # into a QFormLayout.  To hide/show a layout, it must be set in a
        # widget.
        self.home_widget = QWidget()
        self.user_profile_widget = QWidget()
        self.user_admin_widget = QWidget()
        self.add_user_widget = QWidget()
        self.change_password_widget = QWidget()
        
        home_layout = QFormLayout() 
        user_profile_layout = QFormLayout() 
        user_admin_layout = QFormLayout()
        add_user_layout = QFormLayout()
        change_password_layout = QFormLayout()
        
        # Picarro logo
        picarro_logo = QPixmap("logo_picarro.png")
        picarro_label = QLabel("")
        picarro_label.setPixmap(picarro_logo.scaledToHeight(36, Qt.SmoothTransformation))
        logo_box = QHBoxLayout()
        logo_box.addWidget(picarro_label,0,Qt.AlignHCenter)
        
        # Set the form layouts in widgets so hide/show works.
        # Set home form as a the initially visible form.
        self.home_widget.setLayout(home_layout)
        self.user_profile_widget.setLayout(user_profile_layout)
        self.user_admin_widget.setLayout(user_admin_layout)
        self.add_user_widget.setLayout(add_user_layout)
        self.change_password_widget.setLayout(change_password_layout)
        #self.home_widget.hide()
        self.user_profile_widget.hide()
        self.user_admin_widget.hide()
        self.change_password_widget.hide()
        self.add_user_widget.hide()
        
        # Home
        self.input_user_name = QLineEdit()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.returnPressed.connect(self._user_login)
        self.button_user_login = QPushButton("Login")
        self.button_user_login.clicked.connect(self._user_login)
        self.button_cancel_login = QPushButton("Cancel")
        self.button_cancel_login.clicked.connect(self._cancel_login)
        self.label_login_info = QLabel("")
        login_input = QFormLayout()
        login_input.addRow("User Name", self.input_user_name)
        login_input.addRow("Password", self.input_password)
        login_buttons = QHBoxLayout()
        login_buttons.addWidget(self.button_user_login)
        login_buttons.addWidget(self.button_cancel_login)
        home_layout.addRow(login_input)
        home_layout.addRow(login_buttons)
        home_layout.addRow(self.label_login_info)
        
        # User admin widget
        tab_user_manage = QWidget()
        user_manage_layout = QFormLayout()
        tab_user_manage.setLayout(user_manage_layout)
        tab_user_policy = QWidget()
        user_policy_layout = QFormLayout()
        tab_user_policy.setLayout(user_policy_layout)
        tab_user_role = QWidget()
        user_role_layout = QFormLayout()
        tab_user_role.setLayout(user_role_layout)
        self.user_admin_tabs = QTabWidget()
        self.user_admin_tabs.setTabShape(QTabWidget.Triangular)
        self.user_admin_tabs.addTab(tab_user_manage, "User Accounts")
        self.user_admin_tabs.addTab(tab_user_policy, "User Policies")
        self.user_admin_tabs.addTab(tab_user_role, "User Roles")
        button_layout = QHBoxLayout()
        self.button_log_off_user = QPushButton("Log Off")
        self.button_log_off_user.clicked.connect(self._user_log_off)
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_log_off_user)
        user_admin_layout.addRow(self.user_admin_tabs)
        user_admin_layout.addRow(button_layout)
        
        # User management tab
        self.table_user_list = QTableWidget(1, 4)
        self.table_user_list.setMinimumSize(QSize(500, 300))
        self.table_user_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.table_user_list.setAlternatingRowColors(True)
        self.table_user_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_user_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_user_list.verticalHeader().setVisible(False)
        self.table_user_list.setHorizontalHeaderLabels(QString("UserName;Last Name;First Name;Roles").split(";"))
        self.table_user_list.clicked.connect(self._select_user_from_table)
        self.label_user_info = QLabel("")
        self.button_change_pwd = QPushButton("Change Password")
        self.button_change_pwd.clicked.connect(self._change_user_pwd)
        self.button_change_role = QPushButton("Change Role")
        self.menu_user_role = QMenu()
        self.menu_user_role.triggered[QAction].connect(self._process_role_trigger)
        self.button_change_role.setMenu(self.menu_user_role)
        self.button_disable_user = QPushButton("Disable User")
        self.button_disable_user.clicked.connect(self._disable_user)
        self.button_add_user = QPushButton("Add User")
        self.button_add_user.clicked.connect(self._add_user)
        user_info_control = QHBoxLayout()
        user_info_control.addWidget(self.button_change_pwd)
        user_info_control.addStretch(1)
        user_info_control.addWidget(self.button_change_role)
        user_info_control.addStretch(1)
        user_info_control.addWidget(self.button_disable_user)
        user_info_control.addStretch(1)
        user_info_control.addWidget(self.button_add_user)
        user_manage_layout.addRow(self.table_user_list)
        user_manage_layout.addRow(self.label_user_info)
        user_manage_layout.addRow(user_info_control)
        
        # User policies tab
        self.check_password_length = QCheckBox("Password must have at least")
        self.check_password_length.clicked.connect(lambda: self._disable_policy_input("password_length"))
        self.input_password_length = spin_box(value=6, min=6, max=20, step=1)
        self.check_password_mix_charset = QCheckBox("Password must contain numbers, letters and special characters")
        self.check_password_lifetime = QCheckBox("Password expires after")
        self.check_password_lifetime.clicked.connect(lambda: self._disable_policy_input("password_lifetime"))
        self.input_password_lifetime = spin_box(value=182, min=1, max=100000, step=1)
        self.check_password_reuse_period = QCheckBox("New password cannot be one of the previous")
        self.check_password_reuse_period.clicked.connect(lambda: self._disable_policy_input("password_reuse_period"))
        self.input_password_reuse_period = spin_box(value=5, min=1, max=10, step=1)
        self.check_user_login_attempts = QCheckBox("Disable user account after")
        self.check_user_login_attempts.clicked.connect(lambda: self._disable_policy_input("user_login_attempts"))
        self.input_user_login_attempts = spin_box(value=3, min=1, max=100, step=1)
        self.check_user_session_lifetime = QCheckBox("Lock user session after")
        self.check_user_session_lifetime.clicked.connect(lambda: self._disable_policy_input("user_session_lifetime"))
        self.input_user_session_lifetime = spin_box(value=10, min=1, max=100000, step=1)
        self.button_user_save_policy = QPushButton("Save")
        self.button_user_save_policy.clicked.connect(self._save_policy)
        self.button_user_revert_policy = QPushButton("Revert")
        self.button_user_revert_policy.clicked.connect(self._revert_policy)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_user_save_policy)
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_user_revert_policy)
        button_layout.addStretch(1)
        user_policy_layout.addRow(self.check_password_length, control_box("characters",self.input_password_length))
        user_policy_layout.addRow(self.check_password_mix_charset)
        user_policy_layout.addRow(self.check_password_lifetime, control_box("days",self.input_password_lifetime))
        user_policy_layout.addRow(self.check_password_reuse_period, control_box("old passwords",self.input_password_reuse_period))
        user_policy_layout.addRow(self.check_user_login_attempts, control_box("login attempts",self.input_user_login_attempts))
        user_policy_layout.addRow(self.check_user_session_lifetime, control_box("minutes",self.input_user_session_lifetime))
        user_policy_layout.addRow(button_layout)
        
        # User roles tab
        self.input_config_user_role = QComboBox()
        self.list_available_rights = QListWidget()
        self.list_assigned_rights = QListWidget()
        self.button_move_right = QPushButton(">")
        self.button_move_left = QPushButton("<")
        available_right_layout = QVBoxLayout()
        available_right_layout.addWidget(QLabel("Available Rights"))
        available_right_layout.addWidget(self.list_available_rights)
        button_layout = QVBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_move_right)
        button_layout.addWidget(self.button_move_left)
        button_layout.addStretch(1)
        assigned_right_layout = QVBoxLayout()
        assigned_right_layout.addWidget(QLabel("Assigned Rights"))
        assigned_right_layout.addWidget(self.list_assigned_rights)
        list_layout = QHBoxLayout()
        list_layout.addLayout(available_right_layout)
        list_layout.addLayout(button_layout)
        list_layout.addLayout(assigned_right_layout)
        user_role_layout.addRow("User Role", self.input_config_user_role)
        user_role_layout.addRow(list_layout)
        
        # Add new user
        self.input_new_user_name = QLineEdit()
        self.input_new_first_name = QLineEdit()
        self.input_new_last_name = QLineEdit()
        self.input_new_employee_id = QLineEdit()
        self.input_new_phone_num = QLineEdit()
        self.input_new_phone_ext = QLineEdit()
        self.label_curr_password = QLabel("Current Password")
        self.input_curr_password = QLineEdit()
        self.input_curr_password.setEchoMode(QLineEdit.Password)
        self.input_new_password = QLineEdit()
        self.input_new_password.setEchoMode(QLineEdit.Password)
        self.input_new_password2 = QLineEdit()
        self.input_new_password2.setEchoMode(QLineEdit.Password)
        self.input_new_user_role = QComboBox()
        self.button_add_user_next = QPushButton("Next")
        self.button_add_user_next.clicked.connect(self._check_user_input)
        self.button_canel_add_user = QPushButton("Cancel")
        self.button_canel_add_user.clicked.connect(self._canel_add_user)
        self.new_user_info_widget = QWidget()
        user_info = QFormLayout()
        self.new_user_info_widget.setLayout(user_info)
        user_info.addRow("User Name", self.input_new_user_name)
        user_info.addRow("First Name", self.input_new_first_name)
        user_info.addRow("Last Name", self.input_new_last_name)
        user_info.addRow("Employee ID", self.input_new_employee_id)
        user_info.addRow("User Role", self.input_new_user_role)
        user_info.addRow("Phone Number", self.input_new_phone_num)
        user_info.addRow("Phone Extension", self.input_new_phone_ext)
        new_user_control = QHBoxLayout()
        new_user_control.addWidget(self.button_add_user_next)
        new_user_control.addStretch(1)
        new_user_control.addWidget(self.button_canel_add_user)
        add_user_layout.addRow(self.new_user_info_widget)
        add_user_layout.addRow(self.label_curr_password, self.input_curr_password)
        add_user_layout.addRow("New Password", self.input_new_password)
        add_user_layout.addRow("Confirm Password", self.input_new_password2)
        add_user_layout.addRow(new_user_control)
        
        # Main grid layout
        # The row and column stretch help to keep the buttons clustered
        # in the center and also prevent the logo from moving around
        # when the user changes views.
        #
        grid_layout = QGridLayout()
        grid_layout.setColumnStretch(1,1)
        grid_layout.setColumnStretch(3,1)
        grid_layout.setRowStretch(0,2)
        grid_layout.addWidget(self.home_widget,1,2,Qt.AlignHCenter)
        grid_layout.addWidget(self.user_profile_widget,2,2,Qt.AlignHCenter)
        grid_layout.addWidget(self.user_admin_widget,3,2,Qt.AlignHCenter)
        grid_layout.addWidget(self.add_user_widget,4,2,Qt.AlignHCenter)
        grid_layout.addWidget(self.change_password_widget,5,2,Qt.AlignHCenter)
        grid_layout.setRowStretch(6,2)

        main_layout = QVBoxLayout()
        main_layout.addSpacing(25)
        main_layout.addLayout(logo_box)
        main_layout.addLayout(grid_layout)

        centralWidget = QWidget()
        centralWidget.setLayout(main_layout)
        self.setCentralWidget(centralWidget)
    
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
        
    def _get_role_list(self):
        payload = {'command': "get_roles"}
        ret = self._send_request("get", "users", payload, use_token=True, show_error=True)
        if "error" not in ret:
            set_current_roles = set(ret)
            set_old_roles = set(self.role_list)
            if set_old_roles - set_current_roles:
                # if some roles have been removed, we clear all actions in menu
                self.menu_user_role.clear()
                self.input_new_user_role.clear()
                self.input_config_user_role.clear()
                set_old_roles = set()
            for role in set_current_roles-set_old_roles:
                self.menu_user_role.addAction(role)
                self.input_new_user_role.addItem(role)
                self.input_config_user_role.addItem(role)
            self.role_list = ret
        
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
                    self._get_role_list()
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