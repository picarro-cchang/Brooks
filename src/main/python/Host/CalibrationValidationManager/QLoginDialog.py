from PyQt4 import QtGui, QtCore
# import os.path
# import sip
#
# import conf
# from util import censor

# Collection of short prompts

# This is a singleton
class _PromptManager(object):
    # Prompts user for text.
    # This function takes no callbacks and stalls until the user gives a result
    def getDirectory(self, controller, parentDirectory):
        title = "Create Folder"
        label = "Enter a name for the new folder in \""+parentDirectory+"\":"
        result, ok = QtGui.QInputDialog.getText(controller.getMainWindow(), title,
            label, flags=QtCore.Qt.FramelessWindowHint)

        # If user pressed OK
        if ok:
            return result

        # Else implicit None

    # Show error
    def error(self, controller, message):
        self.errorDialog = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Error", message,
            parent = None)

        # Remove borders
        self.errorDialog.setWindowFlags(self.errorDialog.windowFlags() | QtCore.Qt.FramelessWindowHint)

        # Make sure this window is deleted when closed
        self.errorDialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.errorDialog.show()

    # def showFailed(self, controller, files):
    #     self.failedFilesDialogInstance = FailedFilesDialog(controller, files)
    #     return self.failedFilesDialogInstance.exec_()
    #
    # def confirm(self, controller, action, files, destination):
    #     self.confirmDialogInstance = ConfirmDialog(controller, action, files, destination)
    #     return self.confirmDialogInstance.exec_()
    #
    # def ask(self, controller, text, oktext, canceltext):
    #     self.askDialogInstance = AskDialog(controller, text, oktext, canceltext)
    #     return self.askDialogInstance.exec_() == QtGui.QMessageBox.AcceptRole
    #
    # def login(self, controller):
    #     self.loginDialogInstance = LoginDialog(controller)
    #     return self.loginDialogInstance.show()

# Singleton definition
PromptManager = _PromptManager()
#
# # Display a list of files that had errors
# class FailedFilesDialog(QtGui.QDialog):
#     def __init__(self, controller, files):
#         super(FailedFilesDialog, self).__init__(parent = controller.getMainWindow())
#
#         # set up dialog (self)
#         self.setWindowTitle("Errors")
#
#         # Remove borders
#         self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
#
#         # Make sure this window is deleted when closed
#         self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#
#         # Vbox splits text and data
#         self.vbox = QtGui.QVBoxLayout(self)
#         self.setLayout(self.vbox)
#
#         self.header = QtGui.QLabel("Errors were encountered when processing the following files:")
#         self.vbox.addWidget(self.header)
#
#         # List of files
#         self.filelist = QtGui.QListWidget()
#         self.filelist.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
#         for f in files:
#             QtGui.QListWidgetItem(censor(f, controller.getDataDirectory()), self.filelist)
#         self.vbox.addWidget(self.filelist)
#
#         # Add OK button in hbox to align right
#         self.hbox = QtGui.QHBoxLayout()
#         self.hbox.addStretch(1)
#         self.vbox.addLayout(self.hbox)
#         self.buttonOK = QtGui.QPushButton("OK")
#         self.hbox.addWidget(self.buttonOK)
#
#         # Connect ok
#         self.buttonOK.clicked.connect(self.accept)

class QLoginDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        # Create a dialog - no parent, frameless
        super(QLoginDialog, self).__init__(parent = parent,
            flags = QtCore.Qt.FramelessWindowHint)

        self.parent = parent

        # Make this dialog fullscreen to hide the rest of the ui
        self.setWindowState(QtCore.Qt.WindowFullScreen)

        # Set login to Application Modal - stronger than Window Modal
        # Nothing at all should be possible before login
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Make sure this window is deleted when closed
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # hbox to center the vbox
        self.hbox = QtGui.QHBoxLayout(self)
        self.setLayout(self.hbox)

        # Add left Stretch
        self.hbox.addStretch(1)

        # vbox for all info
        self.vbox = QtGui.QVBoxLayout()

        # Add vbox to hbox
        self.hbox.addLayout(self.vbox)

        # And add the right stretch to center the vbox
        self.hbox.addStretch(1)

        # Add a stretch at the top to center everything
        self.vbox.addStretch(1)

        # Picarro logo
        self.picarroLogo = QtGui.QPixmap("icons/logo_picarro.png")
        self.picarroLabel = QtGui.QLabel("")
        self.picarroLabel.setPixmap(self.picarroLogo.scaledToHeight(36, QtCore.Qt.SmoothTransformation))
        self.vbox.addWidget(self.picarroLabel)

        # File Manager text
        self.filemanagerLabel = QtGui.QLabel("<i>System Validation Tool</i>")
        self.filemanagerLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox.addWidget(self.filemanagerLabel)

        # Make the "FileManager" text not too close to the form
        self.vbox.addSpacing(16)

        # Username and password fields
        self.form = QtGui.QFormLayout()

        self.usernameInput = QtGui.QLineEdit()
        self.passwordInput = QtGui.QLineEdit()
        self.passwordInput.setEchoMode(QtGui.QLineEdit.Password)

        self.form.addRow("User Name:", self.usernameInput)
        self.form.addRow("Password:", self.passwordInput)

        self.vbox.addLayout(self.form)

        # Buttons for log in/cancel
        self.buttonHBox = QtGui.QHBoxLayout()
        self.loginButton = QtGui.QPushButton("Login")
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.loginButton.setDefault(True)
        self.buttonHBox.addWidget(self.cancelButton)
        self.buttonHBox.addWidget(self.loginButton)
        self.vbox.addLayout(self.buttonHBox)

        # Stretch at bottom of vbox to center content
        self.vbox.addStretch(1)

        # Functions for actions
        def attemptLogin():
            username = str(self.usernameInput.text())
            password = str(self.passwordInput.text())
            ret = self.parent._db.login(username, password, "CalibrationValidationTool")
            if "error" not in ret:
                self.accept()
            else:
                PromptManager.error(parent, "Username/password not recognized.")

        # Connect dialog reject
        # self.rejected.connect(parent.quit)

        # Connect button events
        self.cancelButton.clicked.connect(self.reject)
        self.loginButton.clicked.connect(attemptLogin)

