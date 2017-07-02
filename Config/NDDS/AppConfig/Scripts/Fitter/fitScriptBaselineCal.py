from numpy import mean, std

ANALYSIS = []
d = DATA

sortedULoss = sorted(d.uncorrectedAbsorbance)
numToTrim = max(1, int(0.05 * len(sortedULoss)))
trimmedULoss = sortedULoss[numToTrim: -numToTrim]
uLossMax = max(trimmedULoss)
uLossMin = min(trimmedULoss)
uLossVar = uLossMax - uLossMin

sortedCLoss = sorted(d.correctedAbsorbance)
numToTrim = max(1, int(0.05 * len(sortedCLoss)))
trimmedCLoss = sortedCLoss[numToTrim: -numToTrim]
cLossMax = max(trimmedCLoss)
cLossMin = min(trimmedCLoss)
cLossVar = cLossMax - cLossMin

RESULT = { "uLossMax":uLossMax, "uLossMin":uLossMin, "uLossVar":uLossVar,
           "cLossMax":cLossMax, "cLossMin":cLossMin, "cLossVar":cLossVar,
           "waveNumber":mean(d.waveNumber),            "freqStd":30e3*std(d.waveNumber),
           "tunerMean":mean(d.tunerValue),             "tunerStd":std(d.tunerValue),
         }

RESULT.update(d.sensorDict)
