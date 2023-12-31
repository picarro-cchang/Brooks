import re
import os
import sys
import time
import traceback
import datetime
from sys import exit
from functools import wraps
from flask import abort, Flask, make_response, Response, request
from flask_restplus import Api, reqparse, Resource, inputs
from flask_security import auth_token_required, Security, utils, current_user
from DataBaseModel import pds
from Host.Common import CmdFIFO
from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Common.timestamp import datetimeToTimestamp
from Host.Common.EventManagerProxy import Log, LogExc, EventManagerProxy_Init
from Host.Common.SharedTypes import RPC_PORT_SUPERVISOR
from Host.Common.AppRequestRestart import RequestRestart
from Host.Common.SingleInstance import SingleInstance

# _DEFAULT_CONFIG_FILE = os.environ["PICARRO_CONF_DIR"] + "/Host/WebServer/SQLiteDataBase.ini"
CONFIG_DIR = os.environ["PICARRO_CONF_DIR"]
AppPath = sys.argv[0]
APP_NAME = "SQLiteServer"
EventManagerProxy_Init(APP_NAME)
app = Flask(__name__, static_url_path='', static_folder='')

api = Api(app, prefix='/api/v1.0', doc='/apidoc')
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PicarroDataBase.sqlite'
app.config['SECURITY_TRACKABLE'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(7)  # 7 days
app.config['SECURITY_TOKEN_MAX_AGE'] = 7 * 24 * 60 * 60  # 7 days
app.config['SECRET_KEY'] = 'picarro'
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxxxxxxxx'


class SQLiteServer(object):
    def __init__(self, dummy=False):
        self.user_login_attempts = {"username": None, "attempts": 0}
        self.supervisor = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % RPC_PORT_SUPERVISOR,
                                                     APP_NAME,
                                                     IsDontCareConnection=False)
        if dummy:  # used for unit testing
            import DummyDataBase
            self.ds = DummyDataBase.DummyDataBase()
            self.load_config_from_database()
        else:
            self.ds = pds

    def load_config_from_ini(self, configFile):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
            self.setup = {
                'host': self.config.get('Setup', "Host_IP", "0.0.0.0"),
                'port': self.config.getint('Setup', "Port", 3600),
                'debug': self.config.getboolean('Setup', "Debug_Mode", True)
            }
        else:
            print "Configuration file not found: %s. Using default settings." % configFile
            # sys.exit(1)
            self.setup = {'host': "0.0.0.0", 'port': 3600, 'debug': False}

    def load_config_from_database(self):
        vars = self.ds.get_all_from_model("system_model")
        self.system_varialbes = {v.name: self._convert_string(v.value) for v in vars}

    def get_request(self, action, api, payload, headers={}):
        request_dict = payload
        # token required
        if api in ["action", "users"] or (api == "system" and action == "post"):
            if "Authentication" not in headers:
                return {"error": "Authentication token required!"}, 401
        # Admin required
        if api == "users" or (api == "action" and action == "get") \
            or (api == "system" and action == "post"):
            roles = [r.name for r in current_user.roles]
            if "Admin" not in roles:
                return {"error": "Admin role required!"}, 403
        if api == "system" and action == "post":
            request_dict["command"] = "save_system_variables"
        elif api == "action" and action == "post":
            request_dict["command"] = "save_action"
        return self.process_request_dict(request_dict)

    def _convert_string(self, s):
        converter = ["float", "int", "lambda x: True if x=='True' else False if x=='False' else 1/0", "str"]
        for c in converter:
            try:
                return eval(c)(s)
            except:
                pass

    def check_login_requester(self, roles, requester):
        # Assign numerical value to role representing permissions level.
        if "Admin" in roles:
            level = 3
        elif "Technician" in roles:
            level = 2
        elif "Operator" in roles:
            level = 1
        else:
            level = 0

        # Validate that the user ("level") is of an adiquate permission level to access the "requester" (application page).
        if requester in ["UserAdmin", "qtLauncher_Config", "NetworkSettingsWidget"] and level < 3:
            return {"error": "Permission denied. Only Admin users can log in."}, 403
        elif (requester == "H2O2Validation" or requester == "CalibrationValidationTool" or requester == "FileManager") and level < 2:
            return {"error": "Permission denied. Only Admin and Technician can log in."}, 403
        return {}

    def check_password(self, username, password):
        responses = []
        ret = self.check_password_length(password)
        if ret:
            return ret
        ret = self.check_password_charset(password)
        if ret:
            return ret
        ret = self.check_password_history(username, password)
        if ret:
            return ret
        return {}  # no error

    def check_password_history(self, username, password):
        period = self.system_varialbes["password_reuse_period"]
        if period >= 0:
            # New password cannot be one of the previous [period] passwords
            history = self.ds.get_password(username)
            if history is not None:
                for idx, p in enumerate(history):
                    if idx >= period:
                        return {}  # no error
                    else:
                        if utils.verify_password(password, p.value):
                            return {"error": "Error in reusing passwords!"}, 409
        return {}  # no error

    def check_password_charset(self, password):
        if self.system_varialbes["password_mix_charset"]:
            errors = []
            # searching for digits
            if re.search(r"\d", password) is None:
                errors.append("Password must contain at least one number!")
            # searching for letters
            if re.search(r"[a-zA-Z]", password) is None:
                errors.append("Password must contain at least one letter!")
            # searching for special symbols
            if password.isalnum():
                errors.append("Password must contain at least one special character!")
            if len(errors) > 0:
                return {"error": "\n".join(errors)}, 422
        return {}  # no error

    def check_password_length(self, password):
        length = self.system_varialbes["password_length"]
        if length >= 0 and len(password) < length:
            return {"error": "Password is too short! Minimum length: %d" % length}, 411
        if len(password) > 15:
            return {"error": "Password is too long! Maximum length: 15."}, 411
        return {}  # no error

    def check_password_age(self, username, password):
        lifetime = self.system_varialbes["password_lifetime"]
        if lifetime >= 0:
            latest_password = self.ds.get_latest_password(username)
            if latest_password is None:
                # accounts created when lifetime < 0 do not have records
                # those accounts are considered "permanent"
                return {}
            td = datetime.datetime.utcnow() - latest_password.created_at
            if (td.days * 86400 + td.seconds) * 1000 + td.microseconds // 1000 > lifetime * 86400000:
                return {"error": "Password expires!"}, 401
        return {}  # no error

    def check_user_login_attempts(self, username):
        # Check to see how many times user fails to login
        # Disable user if attempts exceeds system setting
        if self.system_varialbes["user_login_attempts"] >= 0:
            if username == self.user_login_attempts["username"]:
                self.user_login_attempts["attempts"] += 1
            else:
                self.user_login_attempts = {"username": username, "attempts": 1}
            if self.user_login_attempts["attempts"] >= self.system_varialbes["user_login_attempts"]:
                # disable user
                self.process_request_dict({
                    "command": "update_user",
                    "username": username,
                    "active": 0,
                    "password": None,
                    "roles": None
                })
                return {"error": "Username and password do not match! User account is disabled!"}, 423
            else:
                remain_login = self.system_varialbes["user_login_attempts"] - self.user_login_attempts["attempts"]
                msg = "Username or password are incorrect.\n" + \
                    "You are allowed %d more failed attempts before your account is locked.\n" % (remain_login) + \
                    "If you have forgotten your credentials please contact your account administrator."
                return {"error": msg}, 401
        else:
            return {"error": "Username and password do not match!"}, 401

    def check_phone_number(self, phone_str):
        if phone_str:
            phone_ext = phone_str.split(",")
            if len(phone_ext[0]) > 20:
                return {"error": "Phone number is too long. Maximum length: 20."}, 411
            if len(phone_ext) == 2 and len(phone_ext[1]) > 6:
                return {"error": "Extension number is too long. Maximum length: 6."}, 411
        return {}

    def log_in_user(self, username, password, requester, no_commit=False):
        user = self.ds.find_user(username=username)
        if user is not None:
            if utils.verify_password(password, user.password):
                if not user.active:
                    return {"error": "User is disabled!"}, 423
                if no_commit:
                    # just check password. Do not commit to session
                    return {"user": user}
                ret = self.check_password_age(username, password)
                if ret: return ret
                roles = [role.name for role in user.roles]
                ret = self.check_login_requester(roles, requester)
                if ret: return ret
                utils.login_user(user)
                self.ds.commit()
                self.session_active_time = time.time()
                self.user_login_attempts = {"username": username, "attempts": 0}
                return {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "roles": roles,
                    "token": user.get_auth_token()
                }
            else:
                return self.check_user_login_attempts(username)
        else:
            return {"error": "Username does not exist!"}, 400

    def create_user_account(self, username, request_dict):
        if not username or not request_dict["password"]:
            abort(400)
        if len(username) < 4:
            return {"error": "Username is too short! Minimum length: 4."}, 411
        if len(username) > 64:
            return {"error": "Username is too long! Maximum length: 64."}, 411
        ret = self.check_phone_number(request_dict["phone_number"])
        if ret: return ret
        user = self.ds.find_user(username=username)
        if user:  # User already exists
            return {"error": "Username already exists!"}, 409
        ret = self.check_password(username, request_dict["password"])
        if ret: return ret
        user = self.ds.create_user( \
            username=username,
            last_name=request_dict["last_name"],
            first_name=request_dict["first_name"],
            employee_id=request_dict["employee_id"],
            phone_number=request_dict["phone_number"],
            password=utils.encrypt_password(request_dict["password"]))
        for role in request_dict["roles"].split(","):
            self.ds.add_role_to_user(user, self.ds.find_role(role))
        self.ds.commit()
        self.save_action_history(current_user.username, "create %s as %s" % (username, request_dict["roles"]))
        self.save_password_history(username, request_dict["password"])
        return {"username": username}

    def change_user_password(self, username, password, new_password):
        if new_password is None:
            return {"error": "New password is not specified!"}, 400
        # check password but not log in
        ret = self.log_in_user(username, password, "", no_commit=True)
        for item in ret:
            if "error" in item:
                return ret
                break
        user = ret["user"]
        ret = self.check_password(username, new_password)
        if ret: return ret
        user.password = utils.encrypt_password(new_password)
        self.save_action_history(username, "change password")
        self.save_password_history(username, new_password)
        self.ds.commit()
        return {"username": username}

    def update_user_account(self, username, request_dict):
        if not username:
            return {"error": "Username is not specified!"}, 400
        user = self.ds.find_user(username=username)
        if not user:  # User does not exist
            return {"error": "Username does not exist!"}, 404
        if "active" in request_dict and request_dict["active"] is not None:
            user.active = bool(request_dict["active"])
            a = current_user.username if hasattr(current_user, "username") else "System"
            self.save_action_history(a, "%s is %s" % (username, "enabled" if user.active else "disabled"))
        if "password" in request_dict and request_dict["password"]:
            ret = self.check_password(username, request_dict["password"])
            if ret: return ret
            user.password = utils.encrypt_password(request_dict["password"])
            self.save_action_history(current_user.username, "change %s password" % username)
            self.save_password_history(username, request_dict["password"])
        if "roles" in request_dict and request_dict["roles"]:
            request_roles = request_dict["roles"].split(",")
            for role in user.roles:
                if not role.name in request_roles:
                    self.ds.remove_role_from_user(user, role)
            for role in request_roles:
                if not user.has_role(self.ds.find_role(role)):
                    self.ds.add_role_to_user(user, self.ds.find_role(role))
            self.save_action_history(current_user.username, "set %s role to %s" % (username, request_dict["roles"]))
        self.ds.commit()
        return {"username": username}

    def save_action_history(self, username, action):
        if self.system_varialbes["save_history"]:
            self.ds.save_user_action(username, action)

    def save_password_history(self, username, password):
        if (self.system_varialbes["password_reuse_period"] >= 0) \
                or (self.system_varialbes["password_lifetime"] >= 0):
            self.ds.save_user_password(username, password)

    def save_system_variables(self, request_dict):
        for name in request_dict:
            var = self.ds.find_system_variable(name)
            if var is None:
                self.ds.save_system_variable(name, request_dict[name])
                self.save_action_history(current_user.username, "create system variable %s=%s" % (name, request_dict[name]))
            else:
                new_value = request_dict[name]
                if new_value != var.value:
                    var.value = new_value
                    if new_value == "-1":
                        self.save_action_history(current_user.username, "system variable %s is disabled" % (name))
                    else:
                        self.save_action_history(current_user.username,
                                                 "set system variable %s as %s" % (name.replace('_', ' '), request_dict[name]))
            self.system_varialbes[name] = self._convert_string(request_dict[name])
        self.ds.commit()

    def process_request_dict(self, request_dict):
        cmd = request_dict.pop("command")
        username = request_dict["username"] if "username" in request_dict else None
        if cmd == "change_password":  # AccountAPI, post
            return self.change_user_password(username, request_dict["password"], request_dict["new_password"])
        elif cmd == "create_user":  # UsersAPI, post
            return self.create_user_account(username, request_dict)
        elif cmd == "delete_user":
            user = self.ds.find_user(username=username)
            if not user:
                return {"error": "Username does not exist!"}, 404
            self.ds.delete_user(user)
            self.ds.commit()
            return {"username": username}
        elif cmd == "get_actions":  # ActionAPI, get
            actions = self.ds.get_all_from_model("action_model")
            return [[datetimeToTimestamp(a.taken_at), a.username, a.action] for a in actions]
        elif cmd == "get_all_users":  # UsersAPI, get

            def get_item(foo, item_name):
                res = getattr(foo, item_name)
                return res if res is not None else ""

            users = self.ds.get_all_from_model("user_model")
            return [{
                "username": user.username,
                "last_name": get_item(user, "last_name"),
                "first_name": get_item(user, "first_name"),
                "employee_id": get_item(user, "employee_id"),
                "phone_number": get_item(user, "phone_number"),
                "roles": [role.name for role in user.roles],
                "active": get_item(user, "active")
            } for user in users]
        elif cmd == "get_all_variables":  # SystemAPI, get
            vars = self.ds.get_all_from_model("system_model")
            return {v.name: v.value for v in vars}
        elif cmd == "get_current_user":
            try:
                return {
                    "username": current_user.username,
                    "first_name": current_user.first_name,
                    "last_name": current_user.last_name,
                    "roles": [role.name for role in current_user.roles]
                }
            except:
                return {"error": traceback.format_exc()}, 404
        elif cmd == "get_roles":  # UsersAPI, get
            roles = self.ds.get_all_from_model("role_model")
            return [role.name for role in roles]
        elif cmd == "log_in_user":  # AccountAPI, post
            requester = request_dict["requester"]
            ret = self.log_in_user(username, request_dict["password"], requester)
            status = "succeed"
            for item in ret:
                if "error" in item:
                    status = item["error"]
                    break
            #status = ret["error"] if "error" in ret else "succeed"
            if "Username or password are incorrect" in status:
                status = "Username or password are incorrect"
            self.save_action_history(username, "log in from %s: %s" % (requester, status))
            return ret
        elif cmd == "log_out_user":  # AccountAPI, post
            userInactivity = request_dict["Logout_InActivity"] if "Logout_InActivity" in request_dict else False
            username = current_user.username
            utils.logout_user()
            log_message = "log out from %s" % (request_dict["requester"])
            if userInactivity:
                log_message += " due to inactivity"
            self.save_action_history(username, log_message)
            self.ds.commit()
            return {"status": "succeed"}
        elif cmd == "save_action":  # ActionAPI, post
            self.save_action_history(username, request_dict["action"])
            return {"status": "succeed"}
        elif cmd == "save_system_variables":  # SystemAPI, post
            self.save_system_variables(request_dict)
            return {"status": "succeed"}
        elif cmd == "update_user":  # UsersAPI, post
            ret = self.update_user_account(username, request_dict)
            return ret

    def run(self):
        pass
        #self.startServer()


# Initialize
pds.db.init_app(app)
security = Security(app, pds)
db_server = SQLiteServer()


def any_role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for role in roles:
                if current_user.has_role(pds.find_role(role)):
                    return f(*args, **kwargs)
            abort(403)

        return decorated_function

    return decorator

HELP_STRING = \
"""\
SQLiteServer.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h              Print this help.
-c              Specify a different config file.  Default = "./SQLiteDateBase.ini"
"""


def PrintUsage():
    print HELP_STRING


def HandleCommandSwitches():
    import getopt
    shortOpts = 'h'
    longOpts = ["help", "ini="]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, data:
        print "%s %r" % (data, data)
        sys.exit(1)

    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o, a in switches:
        options[o] = a

    if "/?" in args or "/h" in args:
        options["-h"] = ""

    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    # configFile = "SQLiteDataBase.ini"
    configFile = ""

    if "--ini" in options:
        configFile = os.path.join(CONFIG_DIR, options["--ini"])
    print "Config file specified at command line: %s" % configFile

    return configFile


@app.before_first_request
def before_first_request():
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, "PicarroDataBase.sqlite")
    if not os.path.exists(database_path):
        pds.db.create_all()
        # create default roles
        pds.create_role(name='Admin')
        pds.create_role(name='Technician')
        pds.create_role(name='Operator')
        # create a default admin account
        admin = pds.create_user(username='admin', password=utils.encrypt_password('admin'), phone_number='1-408-962-3900')
        pds.add_role_to_user(admin, pds.find_role("Admin"))
        technician = pds.create_user(username='tech', password=utils.encrypt_password('tech'))
        pds.add_role_to_user(technician, pds.find_role("Technician"))
        operator = pds.create_user(username='operator', password=utils.encrypt_password('operator'))
        pds.add_role_to_user(operator, pds.find_role("Operator"))
        # add default user policies
        default_policies = dict(
            password_length='6',
            password_mix_charset='False',
            password_lifetime='-1',  # days
            password_reuse_period='5',  # times
            user_login_attempts='3',  # times
            user_session_lifetime='10',  # minutes
            save_history='True')
        for p in default_policies:
            var = pds.system_model(p, default_policies[p])
            pds.put(var)
        pds.commit()
    # get configurations from database
    db_server.load_config_from_database()


@api.route('/system')
class SystemAPI(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Commands: get_all_variables")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('_', type=str, required=False, location='form', help='Dictionary containing name-value pairs.')

    @api.expect(get_parser)
    def get(self):
        return db_server.process_request_dict(self.get_parser.parse_args())

    @auth_token_required
    @any_role_required("Admin")
    @api.expect(post_parser)
    def post(self):
        # request.form is an immutable MultiDict
        request_dict = {k: request.form[k] for k in request.form}
        request_dict["command"] = "save_system_variables"
        return db_server.process_request_dict(request_dict)


@api.route('/action')
class ActionAPI(Resource):
    get_parser = reqparse.RequestParser()
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('username', type=str, required=True)
    post_parser.add_argument('action', type=str, required=True)

    @auth_token_required
    @any_role_required("Admin")
    @api.expect(get_parser)
    def get(self):
        request_dict = self.get_parser.parse_args()
        request_dict["command"] = "get_actions"
        return db_server.process_request_dict(request_dict)

    @auth_token_required
    @api.expect(post_parser)
    def post(self):
        request_dict = self.post_parser.parse_args()
        request_dict["command"] = "save_action"
        return db_server.process_request_dict(request_dict)


@api.route('/account')
class AccountAPI(Resource):
    """
    Define functions that do not require token and admin role.
    """
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Commands: get_current_user.")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('username', type=str, required=False, location='form')
    post_parser.add_argument('password', type=str, required=False, location='form')
    post_parser.add_argument('new_password', type=str, required=False, location='form')
    post_parser.add_argument('requester', type=str, required=True, help="Name of request program")
    post_parser.add_argument('Logout_InActivity', type=inputs.boolean, required=False, location='form')
    post_parser.add_argument('command', type=str, required=True, help="Commands: log_in_user, log_out_user, change_password.")

    @api.expect(get_parser)
    def get(self):
        return db_server.process_request_dict(self.get_parser.parse_args())

    @api.expect(post_parser)
    def post(self):
        return db_server.process_request_dict(self.post_parser.parse_args())


@api.route('/users')
class UsersAPI(Resource):
    """
    User management functions. Require token and admin role.
    """
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Commands: get_all_users, get_roles")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('command', type=str, required=True, help="Commands: create_user, update_user")
    post_parser.add_argument('username', type=str, required=True)
    post_parser.add_argument('last_name', type=str, required=False)
    post_parser.add_argument('first_name', type=str, required=False)
    post_parser.add_argument('employee_id', type=str, required=False)
    post_parser.add_argument('phone_number', type=str, required=False)
    post_parser.add_argument('password', type=str, required=False)
    post_parser.add_argument('roles', type=str, required=False)
    post_parser.add_argument('active', type=int, required=False)

    @auth_token_required
    @any_role_required("Admin")
    @api.expect(get_parser)
    def get(self):
        return db_server.process_request_dict(self.get_parser.parse_args())

    @auth_token_required
    @any_role_required("Admin")
    @api.expect(post_parser)
    def post(self):
        return db_server.process_request_dict(self.post_parser.parse_args())


def main():
    my_instance = SingleInstance(APP_NAME)
    if my_instance.alreadyrunning():
        Log("Instance of %s already running" % APP_NAME, Level=2)
    else:
        configFile = HandleCommandSwitches()
        db_server.load_config_from_ini(configFile)
        try:
            db_server.run()
            app.run(**db_server.setup)
        except Exception, e:
            LogExc("Unhandled exception in %s: %s" % (APP_NAME, e), Level=3)
            # Request a restart from Supervisor via RPC call
            restart = RequestRestart(APP_NAME)
            if restart.requestRestart(APP_NAME) is True:
                Log("Restart request to supervisor sent", Level=0)
            else:
                Log("Restart request to supervisor not sent", Level=2)
            # Exit, in case the server running, but the app is not
            # We don't want to get stuck in a restart loop here
            exit(1)


if __name__ == '__main__':
    main()
