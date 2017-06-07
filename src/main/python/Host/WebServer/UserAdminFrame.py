from PyQt4.QtCore import *
from PyQt4.QtGui import *

class UserAdminFrame(QMainWindow):
    """
    Define user interface of UserAdmin program
    """
    def __init__(self, parent=None):
        super(UserAdminFrame, self).__init__(parent)
        
        # Set-up Drop Shadow effect to be used on elements
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setColor(QColor(30,30,30,180))
        self.shadow.setBlurRadius(5)
        
        self.style_data = ""
        with open('styleSheet.qss', 'r') as f:
            self.style_data = f.read()
        self.setStyleSheet(self.style_data)
                
        self.create_widgets()
        self.setWindowTitle("User Management")
        self.resize(800,600)
        
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
        action_history_layout = QVBoxLayout()
        tab_user_role.setLayout(action_history_layout)
        self.user_admin_tabs = QTabWidget()
        self.user_admin_tabs.setTabShape(QTabWidget.Triangular)
        self.user_admin_tabs.addTab(tab_user_manage, "User Accounts")
        self.user_admin_tabs.addTab(tab_user_policy, "User Policies")
        self.user_admin_tabs.addTab(tab_user_role, "User History")
        button_layout = QHBoxLayout()
        self.button_log_off_user = QPushButton("Log Off")
        self.button_log_off_user.clicked.connect(self._user_log_off)
        button_layout.addStretch(1)
        button_layout.addWidget(self.button_log_off_user)
        user_admin_layout.addRow(self.user_admin_tabs)
        user_admin_layout.addRow(button_layout)
        
        # User management tab
        self.table_user_list = QTableWidget(1, 4)
        self.table_user_list.setMinimumSize(QSize(600, 300))
        self.table_user_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        #self.table_user_list.setAlternatingRowColors(True)
        self.table_user_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_user_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_user_list.verticalHeader().setVisible(False)
        self.table_user_list.setHorizontalHeaderLabels(QString("UserName;Last Name;First Name;Roles").split(";"))
        self.table_user_list.clicked.connect(self._select_user_from_table)
        self.label_user_info = QLabel("")
        self.button_change_pwd = QPushButton("Change Pwd")
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
        
        # User history tab
        self.list_action_history = QListWidget()
        self.input_search = QLineEdit()
        self.button_refresh_history = QPushButton("Refresh")
        self.button_refresh_history.clicked.connect(self._get_history)
        action_history_layout.addWidget(self.list_action_history)
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Search:"))
        button_layout.addWidget(self.input_search)
        button_layout.addWidget(self.button_refresh_history)
        action_history_layout.addLayout(button_layout)
                
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