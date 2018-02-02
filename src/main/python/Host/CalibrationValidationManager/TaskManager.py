# TaskManager

from Host.Common.configobj import ConfigObj
from ReferenceGas import ReferenceGas
import pprint

class TaskManager(object):
    def __init__(self, iniFile):
        print("initializing task manager", iniFile)
        self.referenceGases = []
        self.loadConfig()
        return

    def loadConfig(self, iniFile = "task_manager.ini"):
        print("Reading file:", iniFile)
        # co = CustomConfigObj(iniFile)
        co = ConfigObj(iniFile)

        for key, gasConfObj in co["GASES"].items():
            # print("Gas key:%s, dict:%s" %(key,gasConfObj))
            # componentList = gasConfObj.as_list("Components")
            # print("Components:", componentList[0])
            self.referenceGases.append(ReferenceGas(gasConfObj))

        return
