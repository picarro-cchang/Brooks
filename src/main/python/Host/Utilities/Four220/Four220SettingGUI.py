import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from functools import partial
import SerialSettingsIniInterface
import getopt, os, re, copy
from configobj import ConfigObj

if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]
APP_NAME = "Four220SettingUI"


class ChannelSettingWidget(QWidget):
    # Custom signals
    # save - save changes to the ini file
    #
    settingsSaved = pyqtSignal()

    def __init__(self, title = "", parent=None):
        super(ChannelSettingWidget, self).__init__(parent)
        
        """
        ------------------------------------------
        Open external stylesheet and read the data
        ------------------------------------------
        """
        
        self.styleData = ""
        f = open('../styleSheet.qss', 'r')
        self.styleData = f.read()
        f.close()

        
        match = re.search(r'\#(\d)', title)
        ch_num = match.group(1)
        
        self.section_name = 'OUTPUT_CHANNEL' + ch_num
        
        self.setLayout(self.initGUI(title))
        self._connections()
        self._resetWidgets()
        
        
    def initGUI(self, title = ""):

        #self.setStyleSheet(self.styleData)
        innergl = QGridLayout()
        qfl = QFormLayout()

        
        self._airType = QComboBox()
        self._airType.addItems(['NH3','H2O','HF','CavityPressure', 'None'])
        
        self._rangeMin = QLineEdit()
        self._rangeMax = QLineEdit()
        
        
        qfl.addRow(QLabel("Output Type"), self._airType)
        qfl.addRow(QLabel("Range Min"), self._rangeMin)
        qfl.addRow(QLabel("Range Max"), self._rangeMax)
        
        # Action buttons
        self._undoBTN = QPushButton("Undo")
        #self._undoBTN.setDisabled(True)
        self._saveBTN = QPushButton("Save")
        self._saveBTN.setDisabled(True)

        hbl = QHBoxLayout()
        hbl.addWidget(self._undoBTN)
        hbl.addStretch(1)
        hbl.addWidget(self._saveBTN)
        
        #innergl.addWidget(QLabel(title),0,0,Qt.AlignHCenter)
        innergl.addLayout(qfl,0,0)
        innergl.addLayout(hbl,1,0)

        boundingGB = QGroupBox(title)
        boundingGB.setLayout(innergl)

        outerGL = QGridLayout()
        outerGL.addWidget(boundingGB,0,0)
        
        return outerGL
        

    def _connections(self):
        
        self._airType.currentIndexChanged.connect(self.modifyUI)
        
        
        self._rangeMin.textChanged.connect(self.modifyUI)
        #self._rangeMax.textChanged.connect(partial(self._undoBTN.setDisabled, False))
        
        self._rangeMax.textChanged.connect(self.modifyUI)
        #self._rangeMax.textChanged.connect(partial(self._saveBTN.setDisabled, False))
    
        self._undoBTN.clicked.connect(self._resetWidgets)
        self._saveBTN.clicked.connect(self._saveSettings)
        return
        
    def _resetWidgets(self):
        """
        Change the widgets' values to previous saved state.
        """
        source = CONFIG[self.section_name].get('SOURCE')
        idx = self._airType.findText(source, Qt.MatchFixedString)
        if idx >= 0:
            self._airType.setCurrentIndex(idx)
        else:
            self._airType.setCurrentIndex(4)
            
        range_min = CONFIG[self.section_name].get('SOURCE_MIN')
        self._rangeMin.setText(range_min)
        range_max = CONFIG[self.section_name].get('SOURCE_MAX')
        self._rangeMax.setText(range_max)
        self._undoBTN.setDisabled(True)
        self._saveBTN.setDisabled(True)
     
    def _saveSettings(self):
        # convert wiget settings to CONFIG
        if self._airType.currentIndex() == 4:
            for key in CONFIG[self.section_name]:
                CONFIG[self.section_name].update({key : '' })
                
        else:
            if CONFIG[self.section_name].get('SOURCE_MIN') == '' or float(CONFIG[self.section_name].get('SOURCE_MIN')) != float(self._rangeMin.text()):
                CONFIG[self.section_name].update({'SOURCE_MIN': float(self._rangeMin.text())})                
                
            if CONFIG[self.section_name].get('SOURCE_MAX') == '' or float(CONFIG[self.section_name].get('SOURCE_MAX')) != float(self._rangeMax.text()):
                CONFIG[self.section_name].update({'SOURCE_MAX': float(self._rangeMax.text())})
                
            if CONFIG[self.section_name].get('SOURCE') == '' or CONFIG[self.section_name].get('SOURCE') != self._airType.itemText(self._airType.currentIndex()):
                CONFIG[self.section_name].update({'SOURCE' : str(self._airType.itemText(self._airType.currentIndex()))})
        
        self._saveBTN.setDisabled(True)
        self._undoBTN.setDisabled(True)
        
    def modifyUI(self):
        self._undoBTN.setDisabled(False)
        self._saveBTN.setDisabled(False)
        
        if self._airType.itemText(self._airType.currentIndex()) == 'None':
            for w in [self._rangeMin, self._rangeMax]:
                w.clear()
                w.setDisabled(True)
        else:
            for w in [self._rangeMin, self._rangeMax]:
                w.setDisabled(False)



class ChannelSettingsDialog(QDialog):

    def __init__(self, ch0 = True, ch1 = True, ch2 = True, ch3 = True, parent = None):
        super(ChannelSettingsDialog, self).__init__(parent)
        
        self.styleData = ""
        f = open('../styleSheet.qss', 'r')
        self.styleData = f.read()
        f.close()
        self.setStyleSheet(self.styleData)
        
        # Set which widgets to show
        self._ch0 = ch0
        self._ch1 = ch1
        self._ch2 = ch2
        self._ch3 = ch3

        
        self.setLayout(self._initGui())
        self.setConnections()
        self.setModal(True)
        #self.setWindowFlags(Qt.FramelessWindowHint)
        
        return        
        
    def _initGui(self):
        
        self.ch0CSW = ChannelSettingWidget("Channel #0")
        self.ch1CSW = ChannelSettingWidget("Channel #1")
        self.ch2CSW = ChannelSettingWidget("Channel #2")
        self.ch3CSW = ChannelSettingWidget("Channel #3")
        self._cancel = QPushButton("Cancel")
        self._closeBTN = QPushButton("OK")
        
        
        upperHbl = QHBoxLayout()
        if self._ch0:
            upperHbl.addWidget(self.ch0CSW)
        if self._ch1:
            upperHbl.addWidget(self.ch1CSW)
        if self._ch2:
            upperHbl.addWidget(self.ch2CSW)
        if self._ch3:
            upperHbl.addWidget(self.ch3CSW)
        
        lowerHbl = QHBoxLayout()
        lowerHbl.addStretch()
        lowerHbl.addWidget(self._cancel)
        lowerHbl.addWidget(self._closeBTN)
                
        label = QLabel(self)
        label.setText("4-20 mA Output Channels Setting")
        newfont = QFont("Times", 15, QFont.Bold) 
        label.setFont(newfont)
        label.setAlignment(Qt.AlignCenter)
        
        vbl = QVBoxLayout()
        vbl.addWidget(label)
        vbl.addItem(QSpacerItem(30, 30, QSizePolicy.Expanding))
        vbl.addLayout(upperHbl)
        vbl.addLayout(lowerHbl)
        
        return vbl
        
    def setConnections(self):
        self._closeBTN.clicked.connect(self.cleanClose)
        self._cancel.clicked.connect(self.cancel)
        return
    
    def cleanClose(self):

        isSaved = True
        for w in [self.ch0CSW, self.ch1CSW, self.ch2CSW, self.ch3CSW]:
            if w._saveBTN.isEnabled():
                isSaved = False

        if isSaved:
            if CONFIG != ini_CONFIG:
                print "write new values to ini file."
                CONFIG.write()
            self.accept()
        else:
            QMessageBox.warning(
                self, 'Error', 'Save or Undo all channels setting before close')
            
        return
        
    def cancel(self):
        sys.exit()
        
HELP_STRING = """Four220SettingUI.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following:
-h, --help           print this help
-c                   specify a config file:  default = "./4to20Server.ini"
"""

def printUsage():
    print HELP_STRING

def handleCommandSwitches():
    shortOpts = 'hc:s'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = os.path.join(os.path.dirname(AppPath), "4to20Server.ini")
    
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]

    return configFile

configFile = handleCommandSwitches()
CONFIG = ConfigObj(configFile)
ini_CONFIG = copy.deepcopy(CONFIG)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Plastique')#Gives a specific base style - helps with different dev environments
    sd = ChannelSettingsDialog()
    rtn = sd.exec_()
    quit()


