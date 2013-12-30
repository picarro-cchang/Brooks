import time
import math


def speedAsString(value):
    speedConv = 3600.0/1609.344 # m/s to mph
    return "%.1f m/s (%.1f mph)" % (value, value*speedConv)

def etimeAsString(value):
    return time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime(value))

def compToSpeed(x,y):
    return math.sqrt(x*x + y*y)

def durationReduce(etimeList):
    if len(etimeList) > 2:
        interval = (etimeList[-1] - etimeList[0])/(len(etimeList)-1)
        return interval
    else:
        return None

PANEL_LABELS = ["Time of last point", "Data Interval", "System status", "Instrument status", 
                "Car speed", "Wind speed"]

now = time.time()

if INIT:
    savedLastEpochTime = None
    savedLastUpdateTime = None
    savedSinceLastUpdate = 0
    lastEmailTime = 0
    messages = []
    INIT = False

INACTIVE_THRESHOLD = 60
EMAIL_THRESHOLD = 300
EMAIL_INTERVAL = 120
ANALYSIS_POINTS = 50
INTERVAL_THRESHOLD = 2.0
MAX_P3FAILURES = 10

assertAnemometerGood = UTILS.assertMaskedValueEqual(checkVal=0,mask=0x1)

if DATA["type"] == "update":
    if DATA["changed"] == "logData":
        data = DATA["model"].logData
        if data:
            UTILS.show(UTILS.fetch(data, ["EPOCH_TIME"], numPoints=10, reduceFunc=durationReduce), 
                        "Data Interval", "%.2f s", 
                        warningAsserts=UTILS.assertAvailable,
                        errorAsserts=UTILS.assertLimits(maxVal=2.0))
            UTILS.show(UTILS.fetch(data, ["EPOCH_TIME"]), 
                        "Time of last point", etimeAsString, 
                        warningAsserts=(UTILS.assertAvailable, UTILS.assertLimits(minVal=now-EMAIL_THRESHOLD)))
            UTILS.show(UTILS.fetch(data, ["CAR_SPEED"]), 
                        "Car speed", speedAsString,
                        warningAsserts=UTILS.assertAvailable)
            UTILS.show(UTILS.fetch(data, ["INST_STATUS"]), 
                        "Instrument status", "%08x",
                        warningAsserts=UTILS.assertAvailable,
                        errorAsserts=(UTILS.assertMaskedValueEqual(checkVal=0x3c3,mask=0x7FFF),
                                      UTILS.assertMaskedValueNotEqual(checkVal=0x0,mask=0xFFFF0000)))
            UTILS.show(UTILS.fetch(data, ["SYSTEM_STATUS"]), 
                        "System status", "%08x",
                        warningAsserts=UTILS.assertAvailable,
                        errorAsserts=assertAnemometerGood)
            UTILS.show(UTILS.fetch(data, ["WIND_N", "WIND_E"], mapFunc=compToSpeed), 
                        "Wind speed", speedAsString,
                        warningAsserts=UTILS.assertAvailable)
    elif DATA["changed"] == "logFileId":
        data = DATA["model"].logData
        if data:
            msg = "%s: New data log" % etimeAsString(now)
            messages.append(msg)
            UTILS.set("message", msg)
        for panelLabel in PANEL_LABELS:
            UTILS.set("variable", (panelLabel, "", "NORMAL"))
    elif DATA["changed"] == "lastException":
        msg = "%s: %s" % (etimeAsString(now), DATA["model"].lastException)
        messages.append(msg)
        UTILS.set("message", msg, True)
        

elif DATA["type"] == "time":
    sendEmail = False
    if DATA["model"].p3Failures >= MAX_P3FAILURES:
        sendEmail = True
        subject = "PCubed data access error"
    data = DATA["model"].logData
    if data:

        lastEpochTime = UTILS.fetch(data, ["EPOCH_TIME"])
        if not isinstance(lastEpochTime, Exception):
            if lastEpochTime != savedLastEpochTime:
                savedLastUpdateTime = DATA["time"]
                savedLastEpochTime = lastEpochTime
            
            # Calculate the time since the data were updated and the time
            #  since the most recent data were collected. If both are these are
            #  small, we are tracking live data
            
            sinceLastUpdate = DATA["time"] - savedLastUpdateTime
            
            # We detect a transition between an active and an inactive analyzer when 
            #  sinceLastUpdate exceeds INACTIVE_THRESHOLD. 
            if sinceLastUpdate > INACTIVE_THRESHOLD and savedSinceLastUpdate <= INACTIVE_THRESHOLD:
                msg = "%s: Analyzer inactivity detected. Reported time %s." % (etimeAsString(DATA["time"]), etimeAsString(lastEpochTime))
                messages.append(msg)
                UTILS.set("message", msg)
            elif sinceLastUpdate <= INACTIVE_THRESHOLD and savedSinceLastUpdate > INACTIVE_THRESHOLD: 
                msg = "%s: Analyzer activity detected. Reported time %s." % (etimeAsString(DATA["time"]), etimeAsString(lastEpochTime))
                messages.append(msg)
                UTILS.set("message", msg)
            savedSinceLastUpdate = sinceLastUpdate
            #
            # We only consider sending email notifications if sinceLastEpoch is less than EMAIL_THRESHOLD.
            #  
            #
            sinceLastEpoch =  DATA["time"] - savedLastEpochTime
            if sinceLastEpoch < EMAIL_THRESHOLD:
                # Analyze data over last ANALYSIS_POINTS
                nAnemBad = UTILS.fetch(data, ["SYSTEM_STATUS"], mapFunc=assertAnemometerGood,
                          reduceFunc=UTILS.countFalse, numPoints=ANALYSIS_POINTS)
                interval = UTILS.fetch(data, ["EPOCH_TIME"], reduceFunc=durationReduce, numPoints=ANALYSIS_POINTS)
                
                if (nAnemBad > 0) or (interval > INTERVAL_THRESHOLD):
                    msg = "%s: Bad anemometer points = %d, Data interval = %.2f" % (etimeAsString(DATA["time"]), nAnemBad, interval)
                    messages.append(msg)
                    UTILS.set("message", msg)
                if (nAnemBad > ANALYSIS_POINTS/2) or (interval > INTERVAL_THRESHOLD):
                    sendEmail = True
                    subject = "Analyzer alert: %s" % DATA["model"].analyzer
                    
    if sendEmail and (lastEmailTime < now - EMAIL_INTERVAL):
        UTILS.email(subject,"Recent messages:\n%s" % "\n".join(messages))
        UTILS.set("message","Sent email alert at %s" % etimeAsString(now))
        messages = []
        lastEmailTime = now
 