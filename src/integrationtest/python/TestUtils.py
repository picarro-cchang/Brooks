import os
import time
import shutil
import psutil
import subprocess32 as subprocess
import Queue
from Host.Common.TextListener import TextListener
from Host.Common import StringPickler, Listener
from Host.Utilities.BuildHelper.BuildHelper import getBuildFolder

class TestAnalyzer(object):
    def __init__(self, analyzerType, supervisorIni):
        self.analyzerType = analyzerType
        self.supervisorIni = supervisorIni
        self.buildFolder = getBuildFolder()
        self.configDir = os.path.join(self.buildFolder, "../../../", "Config")
        if not os.path.isdir(self.configDir):
            raise Exception("Config fodler not found: %s" % self.configDir)

    def start_analyzer(self):
        # copy AppConfig files into sandbox
        appConfig = os.path.join(self.buildFolder, "AppConfig")
        if os.path.isdir(appConfig):
            shutil.rmtree(appConfig)
        shutil.copytree(os.path.join(self.configDir, self.analyzerType, "AppConfig"), appConfig)
        # copy InstrConfig files into sandbox
        instrConfig = os.path.join(self.buildFolder, "InstrConfig")
        if os.path.isdir(instrConfig):
            shutil.rmtree(instrConfig)
        shutil.copytree(os.path.join(self.configDir, self.analyzerType, "InstrConfig"), instrConfig)
        # copy CommonConfig files into sandbox
        commonConfig = os.path.join(self.buildFolder, "CommonConfig")
        if os.path.isdir(commonConfig):
            shutil.rmtree(commonConfig)
        shutil.copytree(os.path.join(self.configDir, "CommonConfig"), commonConfig)
    
        ### Start analyzer ###
        os.chdir(os.path.join(self.buildFolder, "Host", "pydCaller"))
        args = [
            'xterm', '-e', 
            'python', '-O', 'Supervisor.pyo', '-f', '-c',
            '../../AppConfig/Config/Supervisor/'+self.supervisorIni
        ]
        subprocess.Popen(args)
        print "Analyzer is running..."

    def start_log_listener(self):
        self.measurement = False
        self.error_msg = ""
        self.log_listener = TextListener(None, 40010,
                                         streamFilter=self.log_processor,
                                         retry=True,
                                         name="IntegrationTestListener")

    def log_processor(self, log_text):
        log = log_text.split("|")
        level = float(log[3].strip()[1:])
        if level >= 2.0:
            self.error_msg = "Error in %s: %s" % (log[2], log[5])
        elif level == 1.5:
            if "Measuring" in log[5]:
                self.measurement = True

    def start_data_manager_listener(self, data_source, data_cols):
        self.data_source = data_source
        self.data_cols = data_cols
        self.data_queue = Queue.Queue()
        self.data_manager_listener = Listener.Listener(self.data_queue, 40060,
                                                    StringPickler.ArbitraryObject,
                                                    streamFilter=self.data_processor,
                                                    retry=True,
                                                    name='IntegrationTests')

    def data_processor(self, entry):
        if entry['source'] == self.data_source:
            return {c:entry['data'][c] for c in self.data_cols}
        else:
            return None
    
    def stop_analyzer(self):
        # stop analyzer
        args = ['python', '-O', 'StopSupervisor.pyo', '-o', '1']
        subprocess.Popen(args)
        time.sleep(2)   # give stopsupervisor some time to run
        # delete AppConfig files
        appConfig = os.path.join(self.buildFolder, "AppConfig")
        if os.path.isdir(appConfig):
            shutil.rmtree(appConfig)
        # delete InstrConfig files
        instrConfig = os.path.join(self.buildFolder, "InstrConfig")
        if os.path.isdir(instrConfig):
            shutil.rmtree(instrConfig)
        # delete CommonConfig files
        commonConfig = os.path.join(self.buildFolder, "CommonConfig")
        if os.path.isdir(commonConfig):
            shutil.rmtree(commonConfig)
        # delete Log folder
        log = os.path.join(self.buildFolder, "Log")
        if os.path.isdir(log):
            shutil.rmtree(log)

if __name__ == '__main__':
    t = TestAnalyzer("NCDS", "supervisorSO_simulation.ini")
    t.start_analyzer()