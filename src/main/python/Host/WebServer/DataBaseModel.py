"""
Define models for sqlite database 
"""

from flask_security import SQLAlchemyUserDatastore, Security, utils, UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                            onupdate=db.func.current_timestamp())


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

roles_users = db.Table(
    'roles_users',
    db.Column('user_name', db.Integer(), db.ForeignKey('user.username')),
    db.Column('role_name', db.Integer(), db.ForeignKey('role.name'))
)

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


class PicarroDataStore(SQLAlchemyUserDatastore):
    def __init__(self, db, models):
        SQLAlchemyUserDatastore.__init__(self, db, models["user"], models["role"])
        self.system_model = models["system"]
        self.pwd_model = models["pwd"]
        self.action_model = models["action"]

    def find_system_variable(self, variable_name):
        return self.system_model.query.filter_by(name=variable_name).first()

    def get_all_from_model(self, model_name):
        model = getattr(self, model_name)
        return model.query.all()
    
    def get_password(self, username):
        return self.pwd_model.query.filter_by(username=username).order_by(pds.pwd_model.id.desc())

    def get_latest_password(self, username):
        return self.get_password(username).first()

    def save_system_variable(self, name, value):
        var = self.system_model(name, value)
        self.put(var)
        self.commit()

    def save_user_action(self, username, action):
        a = self.action_model(username, action)
        self.put(a)
        self.commit()

    def save_user_password(self, username, password):
        p = self.pwd_model(username, password)
        self.put(p)
        self.commit()
        
pds = PicarroDataStore(db, 
        {
            "user": User,
            "role": Role,
            "system": SystemVariable,
            "pwd": Password,
            "action": UserAction
        }
    )