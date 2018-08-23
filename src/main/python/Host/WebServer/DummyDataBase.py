import datetime
from flask_security import utils

class Bunch(object):
    """ 
    This class is used to group together a collection as a single object, 
    so that they may be accessed as attributes of that object
    """

    def __init__(self, **kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)

class User(object):
    def __init__(self, username, password, roles):
        self.id = username
        self.username = username
        self.password = utils.encrypt_password(password)
        self.roles = [Bunch(name=role) for role in roles]
        self.active = True
        self.first_name = ""
        self.last_name = ""
        self.employee_id = ""
        self.phone_number = ""

    def get_auth_token(self):
        return "token"

    def get_id(self):
        return self.username

    def has_role(self, role):
        for r in self.roles:
            if r.name == role.name:
                return True
        return False

    def is_active(self):
        return self.active

class DummyDataBase(object):
    def __init__(self):
        self.pwd_model = []
        self.role_model = [Bunch(name="Admin"), Bunch(name="Technician"), Bunch(name="Operator")]
        self.system_model = [
            Bunch(name='password_length', value='6'),
            Bunch(name='password_mix_charset', value='False'),
            Bunch(name='password_lifetime', value='183'),    # days
            Bunch(name='password_reuse_period', value='3'),  # times
            Bunch(name='user_login_attempts', value='3'),    # times
            Bunch(name='user_session_lifetime', value='10'),  # minutes
            Bunch(name='save_history', value='True')
        ]
        self.action_model = []
        self.user_model = [
            User(username="admin",password="admin", roles=["Admin"]),
            User(username="tech",password="tech", roles=["Technician"]),
            User(username="operator",password="operator", roles=["Operator"])
        ]

    def add_role_to_user(self, user, role):
        user.roles.append(role)

    def commit(self):
        pass

    def create_user(self, **kwargs):
        user = Bunch(active=True, roles=[], **kwargs)
        self.user_model.append(user)
        return user

    def delete_user(self, user):
        for idx in range(len(self.user_model)):
            if self.user_model[idx].username == user.username:
                self.user_model.pop(idx)
                return 0

    def find_role(self, role_name):
        for role in self.role_model:
            if role.name == role_name:
                return role
        return None

    def find_system_variable(self, variable_name):
        for var in self.system_model:
            if var.name == variable_name:
                return var
        return None

    def find_user(self, username):
        for user in self.user_model:
            if user.username == username:
                return user
        return None

    def get_all_from_model(self, model_name):
        return getattr(self, model_name)

    def get_password(self, username):
        result = [p for p in self.pwd_model if p.username==username]
        result.reverse()
        return result

    def get_latest_password(self, username):
        length = len(self.pwd_model)
        for idx in range(length-1, -1, -1):
            p = self.pwd_model[idx]
            if p.username == username:
                return p

    def remove_role_from_user(self, user, role):
        for idx in range(len(user.roles)):
            if user.roles[idx].name == role.name:
                user.roles.pop(idx)
                return 0

    def save_system_variable(self, name, value):
        self.system_model.append(
            Bunch(name=name, value=value)
        )

    def save_user_action(self, username, action):
        self.action_model.append(
            Bunch(username=username, action=action, taken_at=datetime.datetime.utcnow())
        )

    def save_user_password(self, username, password, created_time=None):
        if created_time is None:
            created_time = datetime.datetime.utcnow()
        self.pwd_model.append(
            Bunch(username=username, value=password, created_at=created_time)
        )