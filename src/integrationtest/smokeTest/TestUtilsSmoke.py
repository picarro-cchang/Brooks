import os,time,psutil
import subprocess32 as subprocess
import Queue
from Host.Common.TextListener import TextListener
from Host.Common import StringPickler, Listener

class TestAnalyzer(object):
    def __init__(self, analyzerType, supervisorIniAbs):
        self.analyzerType = analyzerType
        self.supervisorIniAbs = supervisorIniAbs
        self.configDir = '/home/picarro/I2000/AppConfig'
        if not os.path.isdir(self.configDir):
            raise Exception("Config folder not found: %s" % self.configDir)

    def start_analyzer(self):
        # Start analyzer #
        path = '/home/picarro/I2000/Host/pydCaller'
        os.chdir(path)
        args = [
            'xterm', '-e', 
            'python', '-O', 'Supervisor.py', '-f', '-c',
            self.supervisorIniAbs
        ]
        #args1 = ['/bin/sh', '/home/picarro/bin/launchBinSimulation.sh']

        subprocess.Popen(args)
        print "Analyzer started"

    def start_log_listener(self):
        self.measurement = False
        self.error_msg = ""
        self.log_listener = TextListener(None, 40010,
                                        streamFilter=self.log_processor,
                                        retry=True,
                                        name="SmokeTestListener")
        

    def log_processor(self, log_text):
        self.log = log_text.split("|")
        print "streamFilter log data:", self.log

    def stop_analyzer(self):
        #stop analyzer
        print "start to stop the analyzer."
        args = ['python', '-O', 'StopSupervisor.py', '-o', '1']
        subprocess.Popen(args)
        time.sleep(2)

if __name__ == '__main__':
    t = TestAnalyzer("NDDS", "/home/picarro/I2000/AppConfig/Config/Supervisor/supervisorSO_simulation.ini")
    t.start_analyzer()
    t.start_log_listener()
    time.sleep(100)
    t.stop_analyzer()
    print "..Done"


        
        
