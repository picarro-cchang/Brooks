from Host.Common.CustomConfigObj import CustomConfigObj

def parsePeriphIntrfConfig(periphIntrfConfig):
    periphCo = CustomConfigObj(periphIntrfConfig, list_values = True)
    rawSource = periphCo.get("SETUP", "RAWSOURCE", "")
    syncSource = periphCo.get("SETUP", "SYNCSOURCE", "")
    rawDict = {"source":rawSource, "data":[]}
    syncDict = {"source":syncSource, "data":[]}
    for s in periphCo.list_sections():
        if s.startswith("PORT"):
            try:
                dataLabels = periphCo.get(s, "DATALABELS", "")
                for col in [data.strip() for data in dataLabels if data.strip()]:
                    rawDict["data"].append(col)
                    syncDict["data"].append(col+"_sync")
            except:
                pass
    return (rawDict, syncDict)