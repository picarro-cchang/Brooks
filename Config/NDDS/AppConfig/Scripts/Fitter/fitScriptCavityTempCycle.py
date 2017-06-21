from numpy import mean, std

ANALYSIS = []
d = DATA

uLossMean = mean(d.uncorrectedAbsorbance)
uLossStd  = std(d.uncorrectedAbsorbance)
try:
    uLossShot2Shot = 100*uLossStd/uLossMean
except:
    uLossShot2Shot = 0

cLossMean = mean(d.correctedAbsorbance)
cLossStd  = std(d.correctedAbsorbance)
try:
    cLossShot2Shot = 100*cLossStd/cLossMean
except:
    cLossShot2Shot = 0

RESULT = { "uLossMean":uLossMean, "uLossStd":uLossStd, "uLossShot2Shot":uLossShot2Shot,
           "cLossMean":cLossMean, "cLossStd":cLossStd, "cLossShot2Shot":cLossShot2Shot,
           "waveNumber":mean(d.waveNumber),            "freqStd":30e3*std(d.waveNumber),
           "tunerMean":mean(d.tunerValue),             "tunerStd":std(d.tunerValue),
         }

RESULT.update(d.sensorDict)
