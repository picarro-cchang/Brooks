from cPickle import loads
from base64 import b64decode
from Host.Common import CmdFIFO, SharedTypes, jsonRpc, timestamp

class JsonRpcTools(object):
    def __init__(self, service_url, auth_user = None, auth_password = None):
        self.jsonRpcService = jsonRpc.Proxy(service_url, auth_user, auth_password)

    def getSeriesRange(self, wfmList, maxDuration):
        """
        Normally, data from the most recent timestamp in the waveforms of wfmList to the current
        time are retrieved, but if this is of greater duration than maxDuration, the interval is
        truncated to [now-maxDuration,now] and clearFlag becomes True.
        """
        tstop = timestamp.getTimestamp()
        minTimestamp = None
        clearFlag = False
        latestTs = {}
        # Examine each waveform for the latest timestamp in that waveform, then find the minimum of these
        #  We ask for data starting from this time, or from the current time - maxDuration. However, since
        #  the result may contain points that are already in some of the waveforms, only those points which
        #  come after the lastestTs for each waveform are added to it.
        for w in wfmList:
            ts = 0
            if w is not None and w.x.count>0:
                ts = timestamp.unixTimeToTimestamp(w.x.GetLatest())
                if minTimestamp is None or ts<minTimestamp: minTimestamp = ts
            latestTs[w] = ts
        tstart = minTimestamp if minTimestamp is not None else 0
        if tstart < tstop - maxDuration:
            tstart = tstop - maxDuration
            clearFlag = True
        range = dict(start=tstart,stop=tstop)
        return range, clearFlag, latestTs.copy()

    def plotSensors(self, wfmList, sensorList, maxDuration):
        """
        Fetch sensor information and update sensor series by calling JSON RPC.
        Return the data obtained.
        """
        range, clearFlag, latestTs = self.getSeriesRange(wfmList,maxDuration)
        params = dict(sensorList=sensorList,range=range,pickle=1)
        result = loads(b64decode(self.jsonRpcService.getSensorData(params)))
        for s,w in zip(sensorList,wfmList):
            if w is not None:
                if clearFlag: w.Clear()
                if s in result:
                    for ts,v in zip(result[s]['timestamp'],result[s][s]):
                        if ts>latestTs[w]: w.Add(timestamp.unixTime(ts),v)
        return result

    def plotData(self, wfm, data, mode, source, maxDuration):
        """
        Fetch analyzer data and update data series by calling JSON RPC.
        This function adds "timestamp" to the JSON-RPC request
        Return the data obtained.
        """
        range, clearFlag, latestTs = self.getSeriesRange([wfm],maxDuration)
        params = dict(mode=mode,source=source,varList=["timestamp",data],range=range,pickle=1)
        result = loads(b64decode(self.jsonRpcService.getDmData(params)))
        if wfm is not None:
            if clearFlag: wfm.Clear()
            for ts,v in result:
                if ts>latestTs[wfm]: wfm.Add(timestamp.unixTime(ts),v)
        return result

    def getLatestDmData(self, mode, source, varList):
        params = dict(mode=mode,source=source,varList=varList,pickle=1)
        result = loads(b64decode(self.jsonRpcService.getLatestDmData(params)))
        return result

    def getDataStruct(self, tstart, tstop):
        """
        Fetch data structure within specified time range by calling JSON RPC.
        """
        range = dict(start=tstart,stop=tstop)
        params = dict(range=range,pickle=1)
        return loads(b64decode(self.jsonRpcService.getDmDataStruct(params)))

    def invokeRPC(self, rpcProxyName, funcName, argTuple):
        """Invoke RPC function calls to communicate with Host software
        """
        params = dict(rpcProxyName=rpcProxyName,funcName=funcName,argTuple=argTuple)
        return self.jsonRpcService.invokeRPC(params)

    def restartHost(self, restartCmd):
        """Restart host software
        """
        params = dict(restartCmd=restartCmd)
        return self.jsonRpcService.restartHost(params)