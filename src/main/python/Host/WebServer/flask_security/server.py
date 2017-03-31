from datetime import timedelta
from functools import wraps
from flask import abort, Flask, make_response, Response, request, render_template, jsonify
from flask_restplus import Api, reqparse, Resource
from flask_security import SQLAlchemyUserDatastore, auth_token_required, Security, utils, current_user, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from wtforms.fields import PasswordField
import os
import sys
import traceback
#import Host.autogen.interface as interface
from Host.Common import CmdFIFO, SharedTypes
import threading
from Host.Common.CustomConfigObj import CustomConfigObj
#from HostInterface import RpcServerThread, DasInterface, DataLoggerInterface, ZMQServerAccess


AppPath = "server.py"
APP_NAME = "SecurityServer"
app = Flask(__name__, static_url_path='', static_folder='../../../../js/SI2000/src/')
     
api = Api(app, prefix='/api/v1.0',  doc='/apidoc', )
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECURITY_TRACKABLE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(7)    # 7 days
app.config['SECURITY_TOKEN_MAX_AGE'] = 7 * 24 * 60 * 60    # 7 days
app.config['SECRET_KEY'] = 'picarro'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_server.sqlite'
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxxxxxxxx'

db = SQLAlchemy(app)

class RpcServerThread(threading.Thread):
    def __init__(self, RpcServer, ExitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.RpcServer = RpcServer
        self.ExitFunction = ExitFunction
    def run(self):
        self.RpcServer.serve_forever()
        try: #it might be a threading.Event
            if self.ExitFunction is not None:
                self.ExitFunction()
            Log("RpcServer exited and no longer serving.")
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")





# A base model for other database tables to inherit
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                            onupdate=db.func.current_timestamp())

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(Base, RoleMixin):
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(Base, UserMixin):
    email = db.Column(db.String(255))
    name = db.Column(db.String(64), unique=True) 
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(45))
    current_login_ip = db.Column(db.String(45))
    login_count = db.Column(db.Integer)
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )

# Initialization
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

@app.before_first_request
def before_first_request():
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, "web_server.sqlite")
    if not os.path.exists(database_path):
        db.create_all()
        user_datastore.create_role(name='Admin')
        user_datastore.create_role(name='Technician')
        admin = user_datastore.create_user(email='admin@picarro.com', name='Picarro', \
            password=utils.encrypt_password('picarro'))
        user_datastore.add_role_to_user(admin, user_datastore.find_role("Admin"))
        technician = user_datastore.create_user(email='someone@samsung.com', name='Samsung', \
            password=utils.encrypt_password('samsung'))
        user_datastore.add_role_to_user(technician, user_datastore.find_role("Technician"))
        db.session.commit()



class WebServer(object):
    def __init__(self, configFile, simulation):
        if os.path.exists(configFile):
            self.config = CustomConfigObj(configFile)
        else:
            print "Configuration file not found: %s" % configFile
            sys.exit(1)
        self.simulation = simulation
        ##self.driver = CmdFIFO.CmdFIFOServerProxy(
            ##"http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER, ClientName = APP_NAME)
        ##self.inst_mgr = CmdFIFO.CmdFIFOServerProxy(
            ##"http://localhost:%d" % SharedTypes.RPC_PORT_INSTR_MANAGER, ClientName = APP_NAME)
        ##self.data_store = ZMQServerAccess(
            ##"tcp://localhost:%s" % SharedTypes.TCP_PORT_DATAMANAGER_ZMQ_PUB )
        ##self.logger = DataLoggerInterface()
        self.loadConfig()
        #self.dasInterface = DasInterface(master=self.simulation_master, driver=None)
        #self.dasInterface = DasInterface(master=None, driver=self.driver)
    	self.startServer()

    def loadConfig(self):
        self.setup = {'host' : self.config.get('Setup', "Host_IP", "0.0.0.0"),
                      'port' : self.config.getint('Setup', "Port", 3000),
                      'debug' : self.config.getboolean('Setup', "Debug_Mode", True)}

    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", SharedTypes.RPC_PORT_FLASK_SERVER),
                                            ServerName = APP_NAME,
                                            ServerDescription = "",
                                            ServerVersion = "1.0.0",
                                            threaded = True)
        self.rpcThread = RpcServerThread(self.rpcServer, None)
        self.rpcThread.start()
        

    def run(self):
        pass
 

HELP_STRING = \
"""\
Server.py [-h] [-c<FILENAME>]

Where the options can be a combination of the following:
-h              Print this help.
-c              Specify a different config file.  Default = "./server.ini"
-s              Simulation mode.
"""

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

def PrintUsage():
    print HELP_STRING
def HandleCommandSwitches():
    import getopt
    shortOpts = 'hc:s'
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

    executeTest = False
    if "-h" in options or "--help" in options:
        PrintUsage()
        sys.exit()

    #Start with option defaults...
    configFile = os.path.dirname(AppPath)  + "server.ini"

    if "-c" in options:
        configFile = options["-c"]
        print "Config file specified at command line: %s" % configFile
    simulation = True if "-s" in options else False

    return (configFile, simulation)



@app.route('/')
def index():
    #return render_template('index.html')
    return "Hello World"

@api.route('/account')
class AccountAPI(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True, help="Should be get_current_user or log_out_user.")
    post_parser = reqparse.RequestParser()
    post_parser.add_argument('email', type=str, required=True, help="User's email", location='form')
    post_parser.add_argument('password', type=str, required=True, location='form')
    post_parser.add_argument('command', type=str, required=True, help="Should be log_in_user.")
    @api.expect(get_parser)
    def get(self):
        request_dict = self.get_parser.parse_args()
        cmd = request_dict["command"]
        print "AccountAPI get request_dict: ", request_dict, "cur user: ", current_user 
        if cmd == "get_current_user":
            try:
                return {"email":current_user.email, "name":current_user.name,
                        "roles":[role.name for role in current_user.roles],
                        "token":current_user.get_auth_token()}
            #except Exception, err:
            except:
                return {"error": traceback.format_exc()}


    @api.expect(post_parser)
    def post(self):
        request_dict = self.post_parser.parse_args()
        cmd = request_dict["command"]
        print "AccountAPI post request_dict: ", request_dict 
        if cmd == "log_in_user":
            user = User.query.filter_by(email=request_dict["email"]).first()
            if user is not None and utils.verify_password(request_dict["password"], user.password):
                utils.login_user(user)
                db.session.commit()
                return {"name":user.name, "email":user.email,
                        "roles":[role.name for role in user.roles],
                        "token":user.get_auth_token()}
            else:
                return {}
        elif cmd == "log_out_user":
            utils.logout_user()
            db.session.commit()
            return {"msg": "you are logged out."}

@api.route('/users')
class UsersAPI(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument('command', type=str, required=True)
    get_parser.add_argument('auth_token', type=str, required=True)

    post_parser = reqparse.RequestParser()
    post_parser.add_argument('command', type=str, required=True, location='form')
    post_parser.add_argument('username', type=str, required=False, location='form')
    post_parser.add_argument('email', type=str, required=False, location='form')
    post_parser.add_argument('password', type=str, required=False, location='form')
    post_parser.add_argument('roles', action='append', required=False, location='form')
    post_parser.add_argument('auth_token', type=str, required=True)


    @api.expect(get_parser)
    @auth_token_required
    @any_role_required("Admin")
    def get(self):
        #parser = reqparse.RequestParser()
        #parser.add_argument('command', type=str, required=True)
        request_dict = self.get_parser.parse_args()
        print "AccountAPI UsersAPI get request_dict: ", request_dict 
        cmd = request_dict["command"]
        if cmd == "get_all":
            users = User.query.all()
            try:
                return [{
                    "name":user.name,
                    "email":user.email,
                    "roles":[role.name for role in user.roles],
                    "active": user.active
                    } for user in users]
            except:
                return {"error": traceback.format_exc()}

        elif cmd == "get_roles":
            roles = Role.query.all()
            try:
                return [role.name for role in roles]
            except:
                return {"error": traceback.format_exc()}

    @api.expect(post_parser)
    @auth_token_required
    @any_role_required("Admin")
    def post(self):
        request_dict = self.post_parser.parse_args()
        print "UsersAPI UsersAPI post request_dict: ", request_dict 
        cmd = request_dict["command"]
        if cmd == "delete":
            user = user_datastore.find_user(name=request_dict["username"])
            if not user:
                abort(406)
            user_datastore.delete_user(user)
            db.session.commit()
            return {}
        elif cmd == "create":
            if not request_dict["username"] or not request_dict["password"]:
                abort(406)
            user = user_datastore.find_user(name=request_dict["username"])
            if user: # User already exists
                abort(409)
            user = user_datastore.create_user(email=request_dict["email"], \
                name=request_dict["username"], \
                password=utils.encrypt_password(request_dict["password"]))
            for role in request_dict["roles"]:
                user_datastore.add_role_to_user(user, user_datastore.find_role(role))
            db.session.commit()
            return {}
        elif cmd == "update":
            if not request_dict["username"]:
                abort(406)
            user = user_datastore.find_user(name=request_dict["username"])
            if not user: # User does not exist
                abort(406)
            user.email = request_dict["email"]
            if request_dict["password"]:
                user.password = utils.encrypt_password(request_dict["password"])
            for role in user.roles:
                if not role.name in request_dict["roles"]:
                    user_datastore.remove_role_from_user(user, role)
            for role in request_dict["roles"]:
                if not user.has_role(user_datastore.find_role(role)):
                    user_datastore.add_role_to_user(user, user_datastore.find_role(role))
            db.session.commit()
            return {}



@api.route('/data-info')
class DataInfoAPI(Resource):
    @auth_token_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('field_hash', type=str, required=False)
        parser.add_argument('analyzer', type=str, required=False)
        parser.add_argument('command', type=str, required=True) # tables or columns

        request_dict = parser.parse_args()
        print "DataInfoAPI get request_dict: ", request_dict 
        nulls = [key for key in request_dict if request_dict[key] is None]
        for key in nulls:
            del request_dict[key]
        return web_server.data_store.submit_request_dict(request_dict)



if __name__ == '__main__':
    web_server = WebServer(*HandleCommandSwitches())
    #web_server.run()
    app.run(**web_server.setup)
