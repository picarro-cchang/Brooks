from ctypes import byref, c_int, c_long, c_short, c_ushort, c_void_p, POINTER, windll
from Host.Common.timestamp import getTimestamp
import time
import numpy as np
from MeasComp import *

if __name__ == "__main__":
    BoardNum = 0
    Count = 10000
    Gain = BIP10VOLTS
    mc = MeasComp()
    ADRes = c_int(0)
    mc.cbGetConfig(BOARDINFO,BoardNum,0,BIADRES,ADRes)
    print "ADRes: ", ADRes.value
    boardType = c_int(0)
    mc.cbGetConfig(BOARDINFO,BoardNum,0,BIBOARDTYPE,boardType)
    print "Board Type: ", boardType.value

    MemHandle = mc.cbWinBufAlloc(Count)
    if MemHandle == 0: raise ValueError("Out of memory")
    ADData = (c_ushort*Count).from_address(MemHandle)

    Gain = BIP5VOLTS
    Options = CONTINUOUS + CONVERTDATA + BACKGROUND

    nChan = 4
    LowChan = 0
    HighChan = nChan-1
    Rate = c_int(10000)
    try:
        ULStat = mc.cbAInScan(BoardNum,LowChan,HighChan,Count,byref(Rate), Gain, MemHandle, Options)
        Status = c_short(RUNNING)
        CurCount = c_ulong(0)
        CurIndex = c_ulong(0)
        lastCount = 0
        lastIndex = 0

        sampleCount = []
        times = []

        totLen = 0
        while Status.value == RUNNING and totLen < 500000:
            time.sleep(0.2)
            ts1 = getTimestamp()
            ULStat = mc.cbGetStatus(BoardNum,byref(Status), byref(CurCount), byref(CurIndex), AIFUNCTION)
            # print CurCount.value, CurIndex.value, Status.value
            ts2 = getTimestamp()
            times.append(0.5*(ts1 + ts2))
            sampleCount.append(CurCount.value)
            curCount = nChan*(CurCount.value // nChan)
            curIndex = nChan*(CurIndex.value // nChan)
            if curCount - lastCount >= Count:
                raise RuntimeError("ADC buffer overrun!")
            # ADC data is from lastIndex to curIndex, wrapping at Count
            if lastIndex < curIndex:
                x = np.asarray(ADData[lastIndex:curIndex])
            else:
                x = np.concatenate((np.asarray(ADData[lastIndex:]),np.asarray(ADData[:curIndex])))
            npts = len(x)
            print npts
            totLen += npts
            lastIndex = (lastIndex + npts) % Count
            lastCount = (lastCount + npts)
    finally:
        ULStat = mc.cbStopBackground(BoardNum,AIFUNCTION)
    mc.cbWinBufFree(MemHandle)
    sampleCount = np.asarray(sampleCount)
    times = np.asarray([t-times[0] for t in times])
    p = np.polyfit(times,sampleCount,1)
    print p
    print np.sqrt(np.mean((np.polyval(p,times)-sampleCount)**2))
