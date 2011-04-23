import os
import threading
from Host.Common import CmdFIFO
from Host.Common.SharedTypes import RPC_PORT_CONFIG_MONITOR
            
APP_NAME = "Configuration Monitor"
APP_DESCRIPTION = "Commit all the configuration changes in repository"
__version__ = 1.0

def toAbsPath(fn):
    def wrapper(self, dir, *args):
        dir = os.path.abspath(dir)
        return fn(self, dir, *args)
    return wrapper
            
class BzrHelper(object):
    @toAbsPath
    def __init__(self, repo):
        if not os.path.isdir(repo):
            os.system(r"bzr init-repo --no-trees %s" % repo)
        self.repo = repo
        self.basePath = os.getcwd()
        
    @toAbsPath
    def isBranch(self, dir):
        info = os.popen(r"bzr info %s" % dir, "r").read()
        if not info:
            return False
        else:
            return True

    @toAbsPath
    def init(self, dir, ignore=""):
        if not os.path.isdir(dir):
            os.makedirs(dir)
        os.chdir(dir)
        os.system(r"bzr init .")
        self._addCommit("Created initial branch")
        if ignore:
            os.system(r"bzr ignore %s" % ignore)
            self._addCommit("Update .bzrignore file")
        os.system(r"bzr push %s" % os.path.join(self.repo, os.path.basename(dir)))
        os.chdir(self.basePath)
     
    @toAbsPath     
    def st(self, dir):
        ret = os.popen(r"bzr st %s" % dir, "r").read()
        return ret
        
    @toAbsPath
    def commit(self, dir, comment="Made some changes"):
        os.chdir(dir)
        self._addCommit(comment)
        os.system(r"bzr push")
        os.chdir(self.basePath)
        
    def _addCommit(self, comment):
        os.system(r"bzr add")
        os.system(r'bzr commit -m "%s" --unchanged' % comment)

class RpcServerThread(threading.Thread):
    def __init__(self, rpcServer, exitFunction):
        threading.Thread.__init__(self)
        self.setDaemon(1) #THIS MUST BE HERE
        self.rpcServer = rpcServer
        self.exitFunction = exitFunction
    def run(self):
        self.rpcServer.serve_forever()
        try: #it might be a threading.Event
            self.exitFunction()
            Log("RpcServer exited and no longer serving.")
            print "RpcServer exited and no longer serving."
        except:
            LogExc("Exception raised when calling exit function at exit of RPC server.")
            print "Exception raised when calling exit function at exit of RPC server."
            
class ConfigMonitor(object):
    def __init__(self, repo):
        self.bzr = BzrHelper(repo)
        self.monitoredDirs = [(r"C:\Picarro\G2000\AppConfig", ""), 
                              (r"C:\Picarro\G2000\InstrConfig", r"C:\Picarro\G2000\InstrConfig\Calibration\*WarmBoxCal*.*")]
        for dir, ignore in self.monitoredDirs:
            if not self.bzr.isBranch(dir):
                self.bzr.init(dir, ignore)
        self.startServer()
        
    def startServer(self):
        self.rpcServer = CmdFIFO.CmdFIFOServer(("", RPC_PORT_CONFIG_MONITOR),
                                                ServerName = APP_NAME,
                                                ServerDescription = APP_DESCRIPTION,
                                                ServerVersion = __version__,
                                                threaded = True)
        self.rpcServer.register_function(self.monitor)
        self.rpcServer.serve_forever()
        
    def monitor(self):
        for dir, ignore in self.monitoredDirs:
            if self.bzr.st(dir):
                self.bzr.commit(dir)
                
if __name__ == "__main__":
    ConfigMonitor(r"C:\Picarro\.private")