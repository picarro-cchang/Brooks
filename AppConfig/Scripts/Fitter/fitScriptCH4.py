from numpy import mean, sqrt
import os.path
import time

def expAverage(xavg,x,n,dxMax):
    if xavg is None: return x
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def initExpAverage(xavg,x,hi,dxMax,count):
    if xavg is None: return x
    n = min(max(count,1),hi)
    y = (x + (n-1)*xavg)/n
    if abs(y-xavg)<dxMax: return y
    elif y>xavg: return xavg+dxMax
    else: return xavg-dxMax
def fitQuality(sdFit,maxPeak,normPeak,sdTau):
    return sqrt(sdFit**2/((maxPeak/normPeak)**2 + sdTau**2))

if INIT:
    fname = os.path.join(BASEPATH,r"./CFADS/spectral library v1_043_CFADS-1_0220.ini")
    loadSpectralLibrary(fname)
    loadPhysicalConstants(fname)
    loadSplineLibrary(fname)
    
    anCH4 = []
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 v2_0 0402.ini")))
    anCH4.append(Analysis(os.path.join(BASEPATH,r"./CFADS/cFADS-1 CH4 FC FY v2_0 0402.ini")))

    ch4_shift = 0
    y_avg = 1.2
    base_avg = 1000
    shift_avg = 0
    avg_count = 1
    last_time = None
    ignore_count = 1
    Ilaserfine = 0
   
init = InitialValues()
deps = Dependencies()
ANALYSIS = []    
d = DATA
d.badRingdownFilter("uncorrectedAbsorbance",minVal=0.50,maxVal=20.0)
d.wlmSetpointFilter(maxDev=0.005,sigmaThreshold=3)
d.sparse(maxPoints=1000,width=0.002,height=100000.0,xColumn="waveNumber",yColumn="uncorrectedAbsorbance",sigmaThreshold=2.5)
d.evaluateGroups(["waveNumber","uncorrectedAbsorbance"])
d.defineFitData(freq=d.groupMeans["waveNumber"],loss=1000*d.groupMeans["uncorrectedAbsorbance"],sdev=1/sqrt(d.groupSizes))
P = d["cavitypressure"]
T = d["cavitytemperature"]
solValves = d.sensorDict["ValveMask"]
dasTemp = d.sensorDict["DasTemp"]
spectrumId = d.sensorDict["SpectrumID"]
etalonTemp = d.sensorDict["EtalonTemp"]
#heaterCurrent = d.sensorDict["Heater_I_mA"]
inletValvePos = d.sensorDict["InletValve"]
outletValvePos = d.sensorDict["OutletValve"]

species = (d.subschemeId & 0x3FF)[0]
init["base",0] = 800

tstart = time.clock()
if species==25:
    try:
        Ilaserfine = 0.01*mean(d.fineLaserCurrent) + 0.99*Ilaserfine
    except:
        pass
    r = anCH4[0](d,init,deps)
    base  = r["base",0]
    y = r[1002,5]
    shift = r["base",3]
    ANALYSIS.append(r)
    if r[1002,2] > 0.005:
        base_avg  = initExpAverage(base_avg,base,500,100,avg_count)
        y_avg     = initExpAverage(y_avg,y,500,0.02,avg_count)
        shift_avg = initExpAverage(shift_avg,shift,500,0.0002,avg_count)
    init["base",0] = base_avg
    init[1002,5]   = y_avg
    init["base",3] = shift_avg
    r = anCH4[1](d,init,deps)

    ANALYSIS.append(r)
    ch4_amp = r[1002,2]
    ch4_conc_raw = 9.8932*r[1002,2]
    ch4_y = y_avg
    ch4_conc_precal = 0.9157*ch4_y*ch4_conc_raw*(140.0/P)
    ch4_peak = r[1002,"peak"]
    ch4_shift = shift_avg
    ch4_res = r["std_dev_res"]
    now = time.clock()
    fit_time = now-tstart
    if last_time != None:
        interval = r["time"]-last_time
    else:
        interval = 0
    last_time = r["time"]

    avg_count += 1
    ignore_count = max(0,ignore_count-1)
    if ignore_count == 0:
        RESULT = {"ch4_res":ch4_res,"ch4_conc_raw":ch4_conc_raw,"ch4_y":ch4_y,"ch4_conc_peak":ch4_peak,
                "ch4_conc_precal":ch4_conc_precal,"ch4_shift":ch4_shift,"ch4_Ilaserfine":Ilaserfine,
                "cavity_pressure":P,"cavity_temperature":T,
                "species":2,"ch4_fit_time":fit_time,"ch4_interval":interval,
                "solenoid_valves":solValves,"das_temp":dasTemp,
                "spectrum_id":spectrumId,"etalon_temp":etalonTemp,
                "inlet_valve_pos":inletValvePos,"outlet_valve_pos":outletValvePos}
    print "CH4 Fit time: %.3f" % (fit_time,) 
