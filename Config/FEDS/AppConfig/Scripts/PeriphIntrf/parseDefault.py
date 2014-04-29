def parseDefault(rawStr):
    retList = []
    for data in rawStr.split(","):
        data = data.replace("\r","")
        data = data.replace("\n","")
        retList.append(eval("0x"+data))
    #pass### ["%10.3f" % ret for ret in retList]
    return retList