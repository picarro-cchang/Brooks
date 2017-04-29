import os
import sys
import traceback
from datetime import timedelta
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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(7)    # 7 days
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
    
    def get_id(self):
        return self.username

# Initialization
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def before_first_request():
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, "PicarroDataBase.sqlite")
    if not os.path.exists(database_path):
        db.create_all()
        # add some data into database
        user_datastore.create_role(name='Admin')
        user_datastore.create_role(name='Technician')
        user_datastore.create_role(name='Operator')
        admin = user_datastore.create_user(username='picarro', \
            password=utils.encrypt_password('picarro'),
            phone_number='1-408-962-3900')
        user_datastore.add_role_to_user(admin, user_datastore.find_role("Admin"))
        technician = user_datastore.create_user(username='samsung',\
            password=utils.encrypt_password('samsung'))
        user_datastore.add_role_to_user(technician, user_datastore.find_role("Technician"))
        operator = user_datastore.create_user(username='someone', \
            password=utils.encrypt_password('someone'))
        user_datastore.add_role_to_user(operator, user_datastore.find_role("Operator"))
        db.session.commit()


class SQLiteServer(object):
    def __init__(self, configFile):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            print "Configuration file not found: %s" % configFile
            sys.exit(1)
        self.loadConfig()
            
    def loadConfig(self):
        self.setup = {'host' : self.config.get('Setup', "Host_IP", "0.0.0.0"),
                      'port' : self.config.getint('Setup', "Port", 3600),
                      'debug' : self.config.getboolean('Setup', "Debug_Mode", True)}
    
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
-c              Specify a different config file.  Default = "./SQLiteDataBase.ini"
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
    configFile = os.path.dirname(AppPath) + "/" + "SQLiteDataBase.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    
    return (configFile, )

db_server = SQLiteServer(*HandleCommandSwitches())

@api.route('/system')
class SystemAPI(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True)
    post_parser = reqparse.RequestParser()
    post_parser.add_argument(
        '_', type=str, required=False, location='form',
        help='Dictionary containing name-value pairs.')
    @api.expect(get_parser)
    def get(self):
        request_dict = self.get_parser.parse_args()
        cmd = request_dict["command"]
        if cmd == "get_all_variables":
            vars = SystemVariable.query.all()
            return {v.name:v.value for v in vars}
    
    @auth_token_required
    @any_role_required("Admin")
    def post(self):
        request_dict = request.form
        for name in request_dict:
            var = SystemVariable.query.filter_by(name=name).first()
            if var is None:
                var = SystemVariable(name, request_dict[name])
                db.session.add(var)
            else:
                var.value = request_dict[name]
        db.session.commit()
            
@api.route('/account')
class AccountAPI(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Should be get_current_user or log_out_user.")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('username', type=str, required=False, location='form')
    post_parser.add_argument('password', type=str, required=False, location='form')
    post_parser.add_argument('command', type=str, required=True, help="Should be log_in_user.")
    @api.expect(get_parser)
    def get(self):
        request_dict = self.get_parser.parse_args()
        cmd = request_dict["command"]
        if cmd == "get_current_user":
            try:
                return {"username":current_user.username, 
                        "first_name":current_user.first_name,
                        "last_name":current_user.last_name,
                        "roles":[role.name for role in current_user.roles]}
            except:
                return {"error": traceback.format_exc()}

    @api.expect(post_parser)            
    def post(self):
        request_dict = self.post_parser.parse_args()
        cmd = request_dict["command"]
        if cmd == "log_in_user":
            user = User.query.filter_by(username=request_dict["username"]).first()
            if user is not None:
                if utils.verify_password(request_dict["password"], user.password):
                    if not user.active:
                        return {"error": "User is disabled!"}
                    else:
                        utils.login_user(user)
                        db.session.commit()
                        return {"username":user.username,
                                "first_name":user.first_name,
                                "last_name":user.last_name,
                                "roles":[role.name for role in user.roles],
                                "token":user.get_auth_token()}
                else:
                    return {"error": "Username and password not match!"}
            else:
                return {"error": "Username not exist!"}
        elif cmd == "log_out_user":
            utils.logout_user()
            db.session.commit()
            return {"status": "you are logged out."}

@api.route('/users')
class UsersAPI(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True)
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('command', type=str, required=True)
    post_parser.add_argument('username', type=str, required=True)
    post_parser.add_argument('last_name', type=str, required=False)
    post_parser.add_argument('first_name', type=str, required=False)
    post_parser.add_argument('last_name', type=str, required=False)
    post_parser.add_argument('employee_id', type=str, required=False)
    post_parser.add_argument('phone_number', type=str, required=False)
    post_parser.add_argument('password', type=str, required=False)
    post_parser.add_argument('roles', type=str, required=False)
    post_parser.add_argument('active', type=int, required=False)
    
    @auth_token_required
    @any_role_required("Admin")
    @api.expect(get_parser)
    def get(self):
        request_dict = self.get_parser.parse_args()
        cmd = request_dict["command"]
        def get_item(foo, item_name):
            res = getattr(foo, item_name)
            return res if res is not None else ""
            
        if cmd == "get_all_users":
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
        elif cmd == "get_roles":
            roles = Role.query.all()
            return [role.name for role in roles]

    @auth_token_required
    @any_role_required("Admin")
    @api.expect(post_parser)
    def post(self):
        request_dict = self.post_parser.parse_args()
        cmd = request_dict["command"]
        username = request_dict["username"]
        if cmd == "delete":
            user = user_datastore.find_user(username=username)
            if not user:
                abort(406)
            user_datastore.delete_user(user)
            db.session.commit()
            return {"username": username}
        elif cmd == "create":
            if not username or not request_dict["password"]:
                abort(406)
            user = user_datastore.find_user(username=username)
            if user: # User already exists
                abort(409)
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
            return {"username": username}
        elif cmd == "update":
            if not username:
                abort(406)
            user = user_datastore.find_user(username=username)
            if not user: # User does not exist
                abort(406)
            if request_dict["active"] is not None:
                user.active = bool(request_dict["active"])
            if request_dict["password"]:
                user.password = utils.encrypt_password(request_dict["password"])
            if request_dict["roles"]:
                request_roles = request_dict["roles"].split(",")
                for role in user.roles:
                    if not role.name in request_roles:
                        user_datastore.remove_role_from_user(user, role)
                for role in request_roles:
                    if not user.has_role(user_datastore.find_role(role)):
                        user_datastore.add_role_to_user(user, user_datastore.find_role(role))
            db.session.commit()
            return {"username": username}

if __name__ == '__main__':
    db_server.run()
    app.run(**db_server.setup)
