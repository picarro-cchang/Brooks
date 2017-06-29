import os
import wx
import unittest
from datetime import datetime
from mockito import patch, unstub
import Host.QuickGui.QuickGui as QuickGui
from Host.WebServer.SQLiteServer import SQLiteServer
from Host.WebServer.SQLiteServer import app as flask_app

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "QuickGui.ini")
app = wx.App(False)

class TestQuickGui(unittest.TestCase):
    def setUp(self):
        QuickGui.AppPath = QuickGui.__file__
        # don't run rpc server
        QuickGui.QuickGui.startServer = lambda x: 0 
        self.gui = QuickGui.QuickGui(CONFIG_FILE)
        self.request_context = flask_app.test_request_context()
        self.request_context.push()
        self.server = SQLiteServer(dummy=True)
        patch(self.gui.sendRequest, self.server.get_request)        
        patch(QuickGui.Dialog.wx.Dialog.ShowModal, self.virtual_dialog)
        patch(QuickGui.Dialog.LoginDialog.getInput, self.get_input)
        patch(QuickGui.Dialog.ChangePasswordDialog.getInput, self.get_input)
        self.dialog_return = []
        self.user_input = []

    def tearDown(self):
        self.request_context.pop()
        unstub()

    def virtual_dialog(self):
        if len(self.dialog_return) > 0:
            return self.dialog_return.pop()
        else:
            return wx.ID_OK

    def get_input(self):
        if len(self.user_input) > 0:
            return self.user_input.pop()
        else:
            return None

    def login_user(self):
        evt = wx.CommandEvent()
        evt.SetEventType(wx.EVT_MENU.typeId)
        self.gui.OnLoginUser(evt)
    
    def test_user_login(self):
        self.user_input = [("admin", "admin")]
        self.assertFalse(self.gui.userLoggedIn)
        self.assertFalse(self.gui.shutdownButton.IsEnabled())
        self.assertTrue(self.gui.userLevel == 0)
        self.login_user()
        self.assertTrue(self.gui.userLoggedIn)
        self.assertTrue(self.gui.shutdownButton.IsEnabled())
        self.assertTrue(self.gui.userLevel == 3)

    def test_password_expire(self):
        self.user_input = [
            ("tech", "tech"), # first login
            ("tech123", "tech123"), # new password
            ("tech", "tech123") # login again using new password
        ]
        self.user_input.reverse()
        self.server.ds.save_user_password("tech", "tech", created_time=datetime(1969,7,20,20,18,0,0))
        self.login_user()
        self.assertTrue(self.gui.userLoggedIn)
        self.assertTrue(self.gui.userLevel == 2)
        self.assertTrue("log in from QuickGui" in self.server.ds.action_model[-1].action)
        self.assertTrue("change password" in self.server.ds.action_model[-2].action)

if __name__ == '__main__':
    unittest.main()