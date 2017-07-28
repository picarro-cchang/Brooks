import os
import time
import unittest
import json
from Host.WebServer.SQLiteServer import db_server, app

from teamcity import is_running_under_teamcity
from teamcity.unittestpy import TeamcityTestRunner

API_PREFIX = '/api/v1.0/'
DATABASE_DIR = './src/main/python/Host/WebServer'

class TestSQLiteServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = os.path.join(DATABASE_DIR, "PicarroDataBase.sqlite")
        config = os.path.join(DATABASE_DIR, "SQLiteDataBase.ini")
        if os.path.exists(db):
            os.remove(db)
        if os.path.exists(config):
            os.remove(config)
            with open(config, "w") as f:
                f.write("[Setup]\n")
                f.write("Host_IP = 0.0.0.0\n")
                f.write("Port = 3600\n")
                f.write("Debug_Mode = False")
        cls.token = None
        cls.server = app.test_client()
        
    @classmethod
    def tearDownClass(cls):
        db = os.path.join(DATABASE_DIR, "PicarroDataBase.sqlite")
        config = os.path.join(DATABASE_DIR, "SQLiteDataBase.ini")
        if os.path.exists(db):
            os.remove(db)
        if os.path.exists(config):
            os.remove(config)
            
    def send_request(self, action, api, payload, use_token=False):
        """
        action: 'get' or 'post'
        use_token: set to True if the api requires token for authentication
        """
        action_func = getattr(self.server, action)
        if use_token and self.token:
            header = {'Authentication': self.token}
        else:
            header = {}
        try:
            response = action_func(API_PREFIX + api, data=payload, headers=header)
            
            return json.loads(response.data)
        except Exception, err:
            return {"error": str(err)}

    def test_0_admin_func(self):
        """
        This test should be run first as the new user created here will be used later
        """
        # log in
        payload = {'command': "log_in_user",
                   'requester': "unittest",
                   'username': "admin", 
                   'password': "admin"}
        ret = self.send_request("post", "account", payload)
        self.assertFalse('error' in ret)
        self.token = ret["token"]
        # create user picarro-technician that will be used in later tests
        payload = {'command': 'create_user', 'username': 'picarro-technician',
                   'password': 'picarro', 'roles': 'Operator'}
        ret = self.send_request("post", "users", payload, use_token=True)
        self.assertTrue("username" in ret)
        # change role
        payload = {'command': 'update_user', 'username': 'picarro-technician',
                   'roles': 'Technician'}
        ret = self.send_request("post", "users", payload, use_token=True)
        self.assertTrue("username" in ret)
        # log out
        payload = {'command': "log_out_user", 'requester': "unittest"}
        ret = self.send_request("post", "account", payload)
        self.assertTrue('succeed' in ret["status"])        
        
    def test_1_multiple_login_attempts(self):
        db_server.system_varialbes["user_login_attempts"] = 1
        # first attempt
        payload = {'command': "log_in_user",
               'requester': "unittest",
               'username': "picarro-technician", 
               'password': "bad-password"}
        ret = self.send_request("post", "account", payload)
        self.assertTrue("password do not match" in ret["error"])
        # second attempt
        payload['password'] = "picarro"
        ret = self.send_request("post", "account", payload)
        self.assertTrue("User is disabled" in ret["error"])
        # log in as admin
        payload = {'command': "log_in_user",
                   'requester': "unittest",
                   'username': "admin", 
                   'password': "admin"}
        ret = self.send_request("post", "account", payload)
        self.assertFalse('error' in ret)
        self.token = ret["token"]
        # reactive user
        payload = {'command': 'update_user', 'username': 'picarro-technician', 'active': 1}
        ret = self.send_request('post', 'users', payload, use_token=True)
        self.assertFalse('error' in ret)
        
    def test_2_password_policy(self):
        db_server.system_varialbes["password_reuse_period"] = 1
        # change password
        payload = {'command': 'change_password', 'username': 'picarro-technician', 
                   'password': 'picarro', 'new_password': 'newpass', 'requester': 'unittest'}
        ret = self.send_request("post", "account", payload)
        self.assertFalse("error" in ret)
        # test case: new password is the same as the old one
        payload['password'] = 'newpass'
        ret = self.send_request("post", "account", payload)
        self.assertTrue("reusing passwords" in ret["error"])
        # test case: short password
        db_server.system_varialbes["password_length"] = 6
        payload['new_password'] = 'new'
        ret = self.send_request("post", "account", payload)
        self.assertTrue("Password is too short" in ret["error"])
        # test case: password has no number
        db_server.system_varialbes["password_mix_charset"] = True
        payload['new_password'] = 'newpassword'
        ret = self.send_request("post", "account", payload)
        self.assertTrue("at least one number" in ret["error"])
        # test case: password has no letter
        payload['new_password'] = '123456'
        ret = self.send_request("post", "account", payload)
        self.assertTrue("at least one letter" in ret["error"])
        # test case: password has no special character
        payload['new_password'] = 'new1234'
        ret = self.send_request("post", "account", payload)
        self.assertTrue("special character" in ret["error"])
        # test case: password expires
        db_server.system_varialbes["password_lifetime"] = 1e-12
        payload2 = {'command': "log_in_user",
               'requester': "unittest",
               'username': "picarro-technician", 
               'password': "newpass"}
        ret = self.send_request("post", "account", payload2)
        self.assertTrue("Password expires" in ret["error"])
        db_server.system_varialbes["password_lifetime"] = 183
        # change back to original password
        db_server.system_varialbes["password_mix_charset"] = False
        payload['new_password'] = 'picarro'
        ret = self.send_request("post", "account", payload)
        self.assertFalse("error" in ret)

if __name__ == '__main__':
    #unittest.main()
    if is_running_under_teamcity():
        print("***********In tamcity unitestcase*****************")
        runner = TeamcityTestRunner()
    else:
        print("***********In normal unitestcase*****************")
        runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)
