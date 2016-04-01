# define function to check if the alarm type specified in 'alarmName' is above or below the value specified in the *ini files
# input alarmParams comes from the Alarm Script and is set in the Alarm*ini files
from json import loads

class Bunch(object):
    """ This class is used to group together a collection as a single object, so that they may be accessed as attributes of that object"""

    def __init__(self, kwds):
        """ The namespace of the object may be initialized using keyword arguments """
        self.__dict__.update(kwds)

    def __call__(self, *args, **kwargs):
        return self.call(self, *args, **kwargs)
        
def loadAlarmParams(alarmParams, section):
    def safe_eval(s):
        try:
            return loads(s)
        except:
            return s
    
    params = alarmParams[section]
    return Bunch({key:safe_eval(params[key]) for key in params})
    
class Alarm(object):
    def __init__(self, alarm, alarmParams, alarmName):
        self.alarm = alarm
        self.alarmName = alarmName
        self.params = alarmParams[alarmName]
        self.word = int(self.params["word"])
        bit = int(self.params["bit"])
        self.mask = 1 << bit

    def checkValue(self, value):
        """
        Check whether value meets conditions set forth in alarmParams[alarmName]
        """
        if value is None:
            return None
        alarmResult = False
        if "above" in self.params:
            alarmResult |= value>float(self.params["above"])
        if "below" in self.params:
            alarmResult |= value<float(self.params["below"])
        if "equal" in self.params:
            alarmResult |= value==float(self.params["equal"])
        if "expression" in self.params:
            try:
                expression = "lambda(x):" + self.params["expression"]
                alarmResult |= eval(expression)(value)
            except:
                pass
        return alarmResult
    
    def setAlarm(self, value):
        """
        Set alarm bit when value is not None
        """
        if value is not None:
            if value:
                self.alarm[self.word] |= self.mask
            else:
                self.alarm[self.word] &= ~self.mask
    
    def processAlarm(self, value, *a):
        """
        Alarm bit is set when value meets conditions set forth in alarmParams[alarmName]
        """
        v = self.processBeforeCheckValue(value, *a)
        v1 = self.checkValue(v)
        v2 = self.processAfterCheckValue(v1, *a)
        self.setAlarm(v2)

    def processBeforeCheckValue(self, value, *a):
        return value
        
    def processAfterCheckValue(self, value, *a):
        return value