from Host.Common.CustomConfigObj import CustomConfigObj

class PeripheralScriptTester(object):
    def __init__(self, scriptFile, configFile, port):
        self.persistentDict = None
        self.parserVersion = 0.0
        scriptCodeObj = compile(file(scriptFile,"r").read().replace("\r",""), scriptFile,"exec")
        dataEnviron = {}
        exec scriptCodeObj in dataEnviron
        if "PARSER_VERSION" in dataEnviron:
            self.parserVersion = dataEnviron["PARSER_VERSION"]
        if self.parserVersion > 0.0:
            self.parserFuncCode = scriptCodeObj
        else:
            self.parserFuncCode = dataEnviron[parserFunc]
        self.config = CustomConfigObj(configFile)
        labelList = [i.strip() for i in self.config.get("PORT%d" % port, "DATALABELS").split(",")]
        if labelList[0]:
            self.dataLabels = labelList
        else:
            self.dataLabels = []
            
    def runScript(self, dataStr):
        if self.parserVersion > 0.0:
            dataEnviron = {"_PERSISTENT_" : self.persistentDict, 
                           "_RAWSTRING_": dataStr,
                           "_DATALABELS_": self.dataLabels}
            exec self.parserFuncCode in dataEnviron
            self.persistentDict = dataEnviron["_PERSISTENT_"]
            return dataEnviron["_OUTPUT_"]
        else:
            # Make it backward compatibility
            return self.parserFuncCode(dataStr)
