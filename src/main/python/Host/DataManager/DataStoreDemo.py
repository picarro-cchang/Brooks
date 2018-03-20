import sys
sys.path.append("/home/picarro/git/host/src/main/python")
import time
from Host.DataManager.DataStore import DataStoreForQt

class GetDataApp():
    def __init__(self):
        self.ds = DataStoreForQt()
        self.wantSensorsStream = False
        return

    def run(self):
        print("Checking for new data a one second intervals")
        while True:
            num_grabbed = self.ds.getQueuedData()
            if num_grabbed > 0:
                try:
                    if self.wantSensorsStream:
                        timeList = self.ds.getList("Sensors","time")
                        pressureList = self.ds.getList("Sensors", "CavityPressure")
                        print("Time:",timeList)
                        print("Pressure:",pressureList)
                    else:
                        timeList = self.ds.getList("analyze_H2O2","time")
                        h2o2List = self.ds.getList("analyze_H2O2", "H2O2")
                        print("Num Update:", num_grabbed)
                        print("Len Time:", len(timeList), " H2O2:", len(h2o2List))
                        print("Time:",timeList)
                        print("[H2O2]:",h2o2List)
                except:
                    pass
            time.sleep(1)
        return

if __name__ == "__main__":
    app = GetDataApp()
    app.run()
    exit()

