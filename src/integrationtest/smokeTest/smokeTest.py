import os,sys, re
import time
import unittest
import configobj

from TestUtilsSmoke import TestAnalyzer

from PyQt4.QtTest import QTest
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import Qt

app = QApplication(sys.argv)
sys.path.insert(0,'/usr/local/picarro/qtLauncher')
import MainWindow
launcher_path = "/usr/local/picarro/qtLauncher"
curpath = os.path.dirname(os.path.realpath(__file__))
match = re.search(r'\/(\w+2000)', curpath)

if match:
    I_model = match.group(1)


class smokeTest(unittest.TestCase):

    def test_00_pre(self):
        #os.system("killall python")
        #os.system("bash /home/picarro/bin/launchSQLServer.sh &")
        os.system("ps aux | grep python | grep -v 'SQL' | grep -v 'smokeTest' |awk '{print $2}' |xargs kill") 
        time.sleep(1)

    def test_00_launcherInstall(self):
        launcher_lst = os.listdir(launcher_path)
        self.assertIsNotNone(launcher_lst)

        if launcher_lst:
            self.assertIn('qtLauncher.py',launcher_lst)
            self.assertIn('launcher.ini',launcher_lst)

    def test_01_launcherGUI(self):
	"""home view displayed correctly"""
        self.window = MainWindow.Window()
        self.assertFalse(self.window.homeBtn.isHidden())
        self.assertFalse(self.window.configBtn.isHidden())
        self.assertFalse(self.window.serviceBtn.isHidden())
        self.assertFalse(self.window.poBtn.isHidden())
        

    def test_02_sqlitServer(self):
        pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
        
        sqlite_server_process_running = False 
        for pid in pids:
            try:
                with open(os.path.join('/proc', pid, 'cmdline'), 'rb') as f:
                    cmd = f.read()
                if "SQLiteServer.py" in cmd:
                    sqlite_server_process_running = True
                    break

            except IOError:
                continue

        self.assertTrue(sqlite_server_process_running)

    def test_03_config(self):
		#QTest.mouseClick(self.window.configBtn, Qt.LeftButton)
        # Only covers the home view and config view.
        self.window = MainWindow.Window()
        self.window._configObj = configobj.ConfigObj(launcher_path + '/launcher.ini')
        
        self.launcherConfigCheckList = []  # a list of boolean vals.

        
        rootDirCheck = ("/"+ I_model) in self.window._configObj["DEFAULT"]['rootDir']
        startButtonLabelCheck = "H2O2" in self.window._configObj["Host_Code_Button"]["button_label"]
        startButtonCaptionCheck = "H<sub>2</sub>O<sub>2</sub>" in self.window._configObj["Host_Code_Button"]["caption"]
        

        # dynamically
        self.binList = os.listdir("/home/picarro/bin/")
        binExists = False
        for script in self.binList:
            #for live analyzer
            #if "launchBin" in script:
            #    binExists = True
            #    break    
            if "launchBinSimulation.sh" in script:
                binExists = True
                break   
        
        self.assertTrue(binExists)
        
        pathOfScriptsCheck = "NDDS" in self.window._configObj["Host_Code_Button"]["args"]
        
        self.launcherConfigCheckList = [(rootDirCheck, "rootDir error"), (startButtonLabelCheck, "start button label error"), 
                                        (startButtonCaptionCheck, "start button caption error"), (pathOfScriptsCheck, "bin scripts path error")]

        launcherWidgets_lst = os.listdir(launcher_path+ '/pQtWidgets')

        if launcherWidgets_lst:
            self.assertIn('ClockInterface.py',launcherWidgets_lst)
            self.assertIn('ClockSettingsWidget.py',launcherWidgets_lst)
            self.assertIn('FourToTwentySettingsWidget.py',launcherWidgets_lst)
            self.assertIn('NetworkInfoDialog.py',launcherWidgets_lst)
            self.assertIn('SerialSettingsIniInterface.py',launcherWidgets_lst)
            self.assertIn('SerialSettingsWidget.py',launcherWidgets_lst)
      
        self.launcherConfigCheckList.append( ("File_Manager_Button" in self.window._configObj, "File_Manager_Button"))
        self.launcherConfigCheckList.append( ("Network" in self.window._configObj, "Network"))
        self.launcherConfigCheckList.append( ("Clock" in self.window._configObj, "Clock"))
        self.launcherConfigCheckList.append( ("Serial" in self.window._configObj, "Serial"))
        self.launcherConfigCheckList.append( ("UserAccounts" in self.window._configObj, "UserAccounts"))
        self.launcherConfigCheckList.append( ("H2O2Validation" in self.window._configObj, "H2O2Validation"))
        self.launcherConfigCheckList.append( ("4-20mA Setting" in self.window._configObj, "4-20mA Setting"))
        

        #check assert
        for item in self.launcherConfigCheckList:
            if not item[0]:
                print "checkItem: ", item[1]
            self.assertTrue(item[0])

    def test_04_config(self):
        #check supervisor config
        supervisor_config = os.listdir('/home/picarro/I2000/AppConfig/Config/Supervisor')
        checkSupervisorIni = "supervisorEXE.ini" in supervisor_config or "supervisorEXE_AMADS_LCT.ini" in supervisor_config
        self.assertTrue(checkSupervisorIni)
    
    def test_05_config(self):
        test_agent = TestAnalyzer("NDDS", "/home/picarro/I2000/AppConfig/Config/Supervisor/supervisorSO_simulation.ini")
        test_agent.start_analyzer()
        #t.start_log_listenr()
        #wait for the warmup process
        time.sleep(20)
        test_agent.start_log_listener()
        while not test_agent.measurement:
            
            time.sleep(2)
        print test_agent.measurement
        test_agent.log_listener.stop()
        time.sleep(20)
        print "stop analyzer"
        test_agent.stop_analyzer()
        print "Done"

        
        

    

               
    







if __name__ == '__main__':
    unittest.main()
