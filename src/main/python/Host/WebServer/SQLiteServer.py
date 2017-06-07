import re
import os
import sys
import time
import traceback
import datetime
from functools import wraps
from flask import abort, Flask, make_response, Response, request, render_template, jsonify
from flask_restplus import Api, reqparse, Resource
from flask_security import SQLAlchemyUserDatastore, auth_token_required, Security, utils, current_user, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from Host.Common.CustomConfigObj import CustomConfigObj

AppPath = sys.argv[0]
APP_NAME = "SQLiteServer"
app = Flask(__name__, static_url_path='', static_folder='')
     
api = Api(app, prefix='/api/v1.0',  doc='/apidoc', )
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///PicarroDataBase.sqlite'
app.config['SECURITY_TRACKABLE'] = False
app.config['SECURITY_CONFIRMABLE'] = False
app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(7)    # 7 days
app.config['SECURITY_TOKEN_MAX_AGE'] = 7 * 24 * 60 * 60    # 7 days
app.config['SECRET_KEY'] = 'picarro'
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxxxxxxxx'

db = SQLAlchemy(app)

# A base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                            onupdate=db.func.current_timestamp())

roles_users = db.Table(
    'roles_users',
    db.Column('user_name', db.Integer(), db.ForeignKey('user.username')),
    db.Column('role_name', db.Integer(), db.ForeignKey('role.name'))
)

class SystemVariable(db.Model):
    name = db.Column(db.String(64), unique=True, primary_key=True)
    value = db.Column(db.String(128))
    
    def __init__(self, name, value):
        self.name = name
        self.value = value
        
class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                 onupdate=db.func.current_timestamp())
    username = db.Column(db.String(64))
    value = db.Column(db.String(255))
    
    def __init__(self, username, value):
        self.username = username
        self.value = utils.encrypt_password(value)
        
class UserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taken_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                 onupdate=db.func.current_timestamp())
    username = db.Column(db.String(64))
    action = db.Column(db.String(128))
    
    def __init__(self, username, action):
        self.username = username
        self.action = action

class Role(Base, RoleMixin):
    name = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(255))

class User(Base, UserMixin):
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(255))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    employee_id = db.Column(db.String(32))
    phone_number = db.Column(db.String(24))
    active = db.Column(db.Boolean())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

# Initialization
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class SQLiteServer(object):
    def __init__(self):
        self.user_login_attempts = {"username":None, "attempts":0}
            
    def load_config_from_ini(self, configFile):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            print "Configuration file not found: %s" % configFile
            sys.exit(1)
        self.setup = {'host' : self.config.get('Setup', "Host_IP", "0.0.0.0"),
                      'port' : self.config.getint('Setup', "Port", 3600),
                      'debug' : self.config.getboolean('Setup', "Debug_Mode", True)}
                      
    def load_config_from_database(self):
        vars = SystemVariable.query.all()
        self.system_varialbes = {v.name: self._convert_string(v.value) for v in vars}
        
    def _convert_string(self, s):
        converter = ["float", "int",
                    "lambda x: True if x=='True' else False if x=='False' else 1/0",
                    "str"]
        for c in converter:
            try:
                return eval(c)(s)
            except:
                pass
                
    def check_password(self, username, password):
        ret = self.check_password_length(password)
        if ret: return ret
        ret = self.check_password_charset(password)
        if ret: return ret
        ret = self.check_password_history(username, password)
        if ret: return ret
        return False    # no error
                
    def check_password_history(self, username, password):
        period = self.system_varialbes["password_reuse_period"]
        if period >= 0:
            # New password cannot be one of the previous [period] passwords
            history = Password.query.filter_by(username=username).order_by(Password.id.desc())
            if history is not None:
                for idx, p in enumerate(history):
                    if idx >= period:
                        return False    # no error
                    else:
                        if utils.verify_password(password, p.value):
                            return {"error": "Error in reusing passwords!"}
        return False    # no error
        
    def check_password_charset(self, password):
        if self.system_varialbes["password_mix_charset"]:
            # searching for digits
            if re.search(r"\d", password) is None:
                return {"error": "Password must contain at least one number!"}
            # searching for letters
            if re.search(r"[a-zA-Z]", password) is None:
                return {"error": "Password must contain at least one letter!"}
            # searching for special symbols
            if password.isalnum():
                return {"error": "Password must contain at least one special character!"}
        return False    # no error
                
    def check_password_length(self, password):
        length = self.system_varialbes["password_length"]
        if length >= 0:
            if len(password) < length:
                return {"error": "Password is too short! Minimum length: %s" % length}
        return False    # no error
        
    def check_password_age(self, username, password):
        lifetime = self.system_varialbes["password_lifetime"]
        if lifetime >= 0:
            latest_password = Password.query.filter_by(username=username).order_by(Password.created_at.desc()).first()
            if latest_password is None:
                # accounts created when lifetime < 0 do not have records
                # those accounts are considered "permanent"
                return False
            td = datetime.datetime.utcnow() - latest_password.created_at
            if (td.days*86400 + td.seconds)*1000 + td.microseconds//1000 > lifetime*86400000:
                return {"error": "Password expires!"}
        return False    # no error                
    
    def check_user_login_attempts(self, username):
        # A simple check to see how many times user fails to login
        # Disable user if attempts exceeds system setting
        # Attempt times is reset to 1 if username is changed.
        if self.system_varialbes["user_login_attempts"] >= 0:
            if username == self.user_login_attempts["username"]:
                self.user_login_attempts["attempts"] += 1
            else:
                self.user_login_attempts = {"username": username, "attempts": 1}
            if self.user_login_attempts["attempts"] >= self.system_varialbes["user_login_attempts"]:
                # disable user
                self.process_request_dict({"command": "update_user", "username": username, 
                    "active": 0, "password": None, "roles": None})
                      
    def log_in_user(self, username, password, no_commit=False):
        user = User.query.filter_by(username=username).first()
        if user is not None:
            if utils.verify_password(password, user.password):
                if not user.active:
                    return {"error": "User is disabled!"}
                if no_commit:
                    # just check password. Do not commit to session
                    return {"user": user}
                ret = self.check_password_age(username, password)
                if ret: return ret
                utils.login_user(user)
                db.session.commit()
                self.session_active_time = time.time()
                return {"username":user.username,
                        "first_name":user.first_name,
                        "last_name":user.last_name,
                        "roles":[role.name for role in user.roles],
                        "token":user.get_auth_token()}
            else:
                self.check_user_login_attempts(username)
                return {"error": "Username and password not match!"}
        else:
            return {"error": "Username not exist!"}
            
    def create_user_account(self, username, request_dict):
        if not username or not request_dict["password"]:
            abort(406)
        user = user_datastore.find_user(username=username)
        if user: # User already exists
            return {"error": "Username already exists!"}
        ret = self.check_password(username, request_dict["password"])
        if ret: return ret                
        user = user_datastore.create_user( \
            username=username,
            last_name=request_dict["last_name"],
            first_name=request_dict["first_name"],
            employee_id=request_dict["employee_id"],
            phone_number=request_dict["phone_number"],
            password=utils.encrypt_password(request_dict["password"]))
        for role in request_dict["roles"].split(","):
            user_datastore.add_role_to_user(user, user_datastore.find_role(role))
        db.session.commit()
        self.save_action_history(current_user.username, "create %s as %s" % (username, request_dict["roles"]))
        self.save_password_history(username, request_dict["password"])
        return {"username": username}
        
    def change_user_password(self, username, password, new_password):
        if new_password is None:
            return {"error": "New password not specified!"}
        # check password but not log in
        ret = self.log_in_user(username, password, no_commit=True)
        if "error" in ret:
            return ret
        user = ret["user"]
        ret = self.check_password(username, new_password)
        if ret: return ret
        user.password = utils.encrypt_password(new_password)
        self.save_action_history(username, "change password")
        self.save_password_history(username, new_password)
        db.session.commit()
        return {"username": username}
            
    def update_user_account(self, username, request_dict):
        if not username:
            return {"error": "Username not specified!"}
        user = user_datastore.find_user(username=username)
        if not user: # User does not exist
            return {"error": "Username not exists!"}
        if request_dict["active"] is not None:
            user.active = bool(request_dict["active"])
            a = current_user.username if hasattr(current_user, "username") else "System"
            self.save_action_history(a, "set %s active to %s" % (username, user.active))
        if request_dict["password"]:
            ret = self.check_password(username, request_dict["password"])
            if ret: return ret
            user.password = utils.encrypt_password(request_dict["password"])
            self.save_action_history(current_user.username, "change %s password" % username)
            self.save_password_history(username, request_dict["password"])
        if request_dict["roles"]:
            request_roles = request_dict["roles"].split(",")
            for role in user.roles:
                if not role.name in request_roles:
                    user_datastore.remove_role_from_user(user, role)
            for role in request_roles:
                if not user.has_role(user_datastore.find_role(role)):
                    user_datastore.add_role_to_user(user, user_datastore.find_role(role))
            self.save_action_history(current_user.username, "set %s roles to %s" % (username, request_dict["roles"]))
        db.session.commit()
        return {"username": username}
           
    def save_action_history(self, username, action):
        if self.system_varialbes["save_history"]:
            a = UserAction(username, action)
            db.session.add(a)
            db.session.commit()
            
    def save_password_history(self, username, password):
        if (self.system_varialbes["password_reuse_period"] >= 0) \
                or (self.system_varialbes["password_lifetime"] >= 0):
            p = Password(username, password)
            db.session.add(p)
            db.session.commit()
    
    def process_request_dict(self, request_dict):
        cmd = request_dict.pop("command")
        username = request_dict["username"] if "username" in request_dict else None
        if cmd == "change_password":    # AccountAPI, post
            return self.change_user_password(username, request_dict["password"], request_dict["new_password"])
        elif cmd == "create_user":    # UsersAPI, post
            return self.create_user_account(username, request_dict)
        elif cmd == "delete_user":
            user = user_datastore.find_user(username=username)
            if not user:
                return {"error": "Username not exists!"}
            user_datastore.delete_user(user)
            db.session.commit()
            return {"username": username}
        elif cmd == "get_actions":      # ActionAPI, get
            actions = UserAction.query.all()
            return [[a.taken_at.strftime("%Y-%m-%d %H:%M:%S"), a.username, a.action] for a in actions]
        elif cmd == "get_all_users":    # UsersAPI, get
            def get_item(foo, item_name):
                res = getattr(foo, item_name)
                return res if res is not None else ""
                
            users = User.query.all()
            return [{
                "username": user.username,
                "last_name": get_item(user, "last_name"),
                "first_name": get_item(user, "first_name"),
                "employee_id": get_item(user, "employee_id"),
                "phone_number": get_item(user, "phone_number"),
                "roles": [role.name for role in user.roles],
                "active": get_item(user, "active")
                } for user in users]
        elif cmd == "get_all_variables":    # SystemAPI, get
            vars = SystemVariable.query.all()
            return {v.name:v.value for v in vars}
        elif cmd == "get_current_user":
            try:
                return {"username":current_user.username, 
                        "first_name":current_user.first_name,
                        "last_name":current_user.last_name,
                        "roles":[role.name for role in current_user.roles]}
            except:
                return {"error": traceback.format_exc()}
        elif cmd == "get_roles":    # UsersAPI, get
            roles = Role.query.all()
            return [role.name for role in roles]
        elif cmd == "log_in_user":  # AccountAPI, post
            ret = self.log_in_user(username, request_dict["password"])
            status = ret["error"] if "error" in ret else "succeed"
            self.save_action_history(username, "log in from %s: %s" % (request_dict["requester"], status))
            return ret
        elif cmd == "log_out_user": # AccountAPI, post
            username = current_user.username
            utils.logout_user()
            self.save_action_history(username, "log out from %s" % (request_dict["requester"]))
            db.session.commit()
            return {"status": "succeed"}
        elif cmd == "save_action":  # ActionAPI, post
            save_action_history(username, request_dict["action"])
            return {"status": "succeed"}
        elif cmd == "save_system_variables":    # SystemAPI, post
            for name in request_dict:
                var = SystemVariable.query.filter_by(name=name).first()
                if var is None:
                    var = SystemVariable(name, request_dict[name])
                    db.session.add(var)
                else:
                    var.value = request_dict[name]
                self.system_varialbes[name] = self._convert_string(request_dict[name])
            db.session.commit()
            return {"status": "succeed"}
        elif cmd == "update_user":  # UsersAPI, post
            ret = self.update_user_account(username, request_dict)
            return ret
    
    def run(self):
        pass
        #self.startServer()

def any_role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            for role in roles:
                if current_user.has_role(user_datastore.find_role(role)):
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
    shortOpts = 'hc:'
    longOpts = ["help"]
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
    configFile = "SQLiteDataBase.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    
    return configFile

db_server = SQLiteServer()

@app.before_first_request
def before_first_request():
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, "PicarroDataBase.sqlite")
    if not os.path.exists(database_path):
        db.create_all()
        # create default roles
        user_datastore.create_role(name='Admin')
        user_datastore.create_role(name='Technician')
        user_datastore.create_role(name='Operator')
        # create a default admin account
        admin = user_datastore.create_user(username='admin', \
            password=utils.encrypt_password('admin'),
            phone_number='1-408-962-3900')
        user_datastore.add_role_to_user(admin, user_datastore.find_role("Admin"))
        technician = user_datastore.create_user(username='tech',\
            password=utils.encrypt_password('tech'))
        user_datastore.add_role_to_user(technician, user_datastore.find_role("Technician"))
        operator = user_datastore.create_user(username='operator', \
            password=utils.encrypt_password('operator'))
        user_datastore.add_role_to_user(operator, user_datastore.find_role("Operator"))
        # add default user policies
        default_policies = dict(
            password_length='6',
            password_mix_charset='False',
            password_lifetime='183',    # days
            password_reuse_period='3',  # times
            user_login_attempts='3',    # times
            user_session_lifetime='10',  # minutes
            save_history='True'
        )
        for p in default_policies:
            var = SystemVariable(p, default_policies[p])
            db.session.add(var)
        db.session.commit()
    # get configurations from database
    db_server.load_config_from_database()

@api.route('/system')
class SystemAPI(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Commands: get_all_variables")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument(
        '_', type=str, required=False, location='form',
        help='Dictionary containing name-value pairs.')
    @api.expect(get_parser)
    def get(self):
        return db_server.process_request_dict(self.get_parser.parse_args())
    
    @auth_token_required
    @any_role_required("Admin")
    def post(self):
        request_dict = request.form
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
    @any_role_required("Admin")
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
        

if __name__ == '__main__':
    configFile = HandleCommandSwitches()
    db_server.load_config_from_ini(configFile)
    db_server.run()
    app.run(**db_server.setup)