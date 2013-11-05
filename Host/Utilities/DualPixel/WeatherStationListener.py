from collections import deque
from numpy import *
import tables
import time
import zmq
from Host.autogen import interface
from Host.Common import SharedTypes, StringPickler


class WindDataTableType(tables.IsDescription):
    time = tables.Int64Col()
    ws_lon = tables.Float32Col()
    ws_lat = tables.Float32Col()
    ws_cos_head = tables.Float32Col()
    ws_sin_head = tables.Float32Col()


class WeatherStationListener(object):

    def __init__(self, ipAddr, port):
        self.context = zmq.Context()
        self.listenSock = self.context.socket(zmq.SUB)
        self.listenSock.connect("tcp://%s:%d" % (ipAddr, port))
        self.listenSock.setsockopt(zmq.SUBSCRIBE, "")
        self.saveHandle = None
        self.saveTable = None
        self.saveFname = ''
        self.latestTimestamp = None

    def setSaveFile(self, name):
        self.saveFname = name
        self.saveHandle = tables.openFile(
            self.saveFname, mode='w', title="Weather Station Data")
        self.saveTable = self.saveHandle.createTable(
            self.saveHandle.root, "windData", WindDataTableType)

    def closeSaveFile(self):
        if self.saveTable is not None:
            self.saveTable.flush()
            self.saveTable = None
        if self.saveHandle:
            self.saveHandle.close()
            print "Closing weather station file"
            self.saveHandle = None
            self.saveFname = ''

    def saveAndFetch(self):
        try:
            data = self.listenSock.recv(zmq.DONTWAIT)
            res = StringPickler.UnPackArbitraryObject(data)[0]
            if res['source'] not in ["parseWeatherStation"] or not res['good']:
                return None
            windDict = res['data']
            self.latestTimestamp = windDict["timestamp"]
            if self.saveTable is not None:
                row = self.saveTable.row
                row['time'] = windDict["timestamp"]
                row['ws_lon'] = windDict["WS_WIND_LON"]
                row['ws_lat'] = windDict["WS_WIND_LAT"]
                row['ws_cos_head'] = windDict["WS_COS_HEADING"]
                row['ws_sin_head'] = windDict["WS_SIN_HEADING"]
                row.append()
            return windDict
        except zmq.ZMQError:
            return None

    def getAvailableData(self, deque, maxLength):
        # Store the data and the cumulative sums so that we can easily find running means of velocity
        #  and the Yamartino standard deviation
        while True:
            windDict = self.saveAndFetch()
            if not windDict:
                break
            wlon = windDict["WS_WIND_LON"]
            wlat = windDict["WS_WIND_LAT"]
            wtot = sqrt(wlon * wlon + wlat * wlat) + 1.e-5
            wcos = wlon / wtot
            wsin = wlat / wtot
            newDat = array([wlon, wlat, wcos, wsin,
                            windDict["WS_COS_HEADING"], windDict["WS_SIN_HEADING"]])
            if len(deque) == 0:
                deque.append((windDict["timestamp"], newDat, newDat.copy()))
            else:
                _, _, s = deque[-1]
                deque.append((windDict["timestamp"], newDat, s + newDat))
            while len(deque) > maxLength:
                deque.popleft()

    def getLocalStats(self, deque, interval, timestamps):
        # Calculate the running mean velocity, running mean wind bearing, running mean anemometer heading
        #  and Yamartino standard deviation at the list of timestamps specified.  All angles are in degrees
        # The "interval" parameter (even) is the number of samples that the
        # statistics are computed over.
        where = digitize(timestamps, [ts for ts, _, _ in deque])
        values = unique(where)
        i2 = interval // 2
        averages = {}
        for v in values:
            iu = min(v + i2, len(deque) - 1)
            il = max(v - i2, 0)
            tu, _, upperSum = deque[iu]
            tl, _, lowerSum = deque[il]
            # Calculate averages over the interval
            if iu > il:
                averages[v] = (upperSum - lowerSum) / float(iu - il)
            else:
                averages[v] = asarray(6 * [NaN])

        wlon = asarray([averages[w][0] for w in where])
        wlat = asarray([averages[w][1] for w in where])
        wcos = asarray([averages[w][2] for w in where])
        wsin = asarray([averages[w][3] for w in where])
        hcos = asarray([averages[w][4] for w in where])
        hsin = asarray([averages[w][5] for w in where])
        eps = sqrt(1.0 - wsin ** 2 - wcos ** 2)
        ystd = (180.0 / pi) * arcsin(eps) * \
            (1 + (2.0 / sqrt(3) - 1) * eps ** 3)
        return wlon, wlat, tobearing(wsin, wcos), tobearing(hsin, hcos), ystd


if __name__ == "__main__":
    ipAddr = '10.100.3.105'
    port = 45065
    d = deque()
    wsl = WeatherStationListener(ipAddr, port)
    wsl.setSaveFile('weather.h5')
    for i in range(30):
        time.sleep(1.0)
        wsl.getAvailableData(d, 100)
        print i
    wsl.closeSaveFile()
    print d
