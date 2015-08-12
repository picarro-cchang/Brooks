# define function to check if the alarm type specified in 'alarmName' is above or below the value specified in the *ini files
# input alarmParams comes from the Alarm Script and is set in the Alarm*ini files
def alarmValue(alarms, alarmParams, alarmName, value):
    word = int(alarmParams[alarmName]["word"])
    bit = int(alarmParams[alarmName]["bit"])

    alarmResult = False
    if "above" in alarmParams[alarmName]:
        alarmResult = alarmResult or value>float(alarmParams[alarmName]["above"])

    if "below" in alarmParams[alarmName]:
        alarmResult = alarmResult or value<float(alarmParams[alarmName]["below"])

    mask = 1 << bit
    if alarmResult:
        alarms[word] |= mask
    else:
        alarms[word] &= ~mask