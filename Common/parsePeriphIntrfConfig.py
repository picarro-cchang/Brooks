from Host.Common.CustomConfigObj import CustomConfigObj

def parsePeriphIntrfConfig(periphIntrfConfig):
    periphCo = CustomConfigObj(periphIntrfConfig)
    rawDict = {"source":[], "data":[]}
    syncDict = {"source":[], "data":[]}
    try:
        for src in [s.strip() for s in periphCo.get("SETUP", "RAWSOURCE", "").split(",") if s.strip()]:
            rawDict["source"].append(src)
    except:
        pass
        
    try:
        for src in [s.strip() for s in periphCo.get("SETUP", "SYNCSOURCE", "").split(",") if s.strip()]:
            syncDict["source"].append(src)
    except:
        pass
        
    for s in periphCo.list_sections():
        if s.startswith("PORT"):
            try:
                for col in [c.strip() for c in periphCo.get(s, "DATALABELS", "").split(",") if c.strip()]:
                    rawDict["data"].append(col)
                    syncDict["data"].append(col+"_sync")
            except:
                pass

    return (rawDict, syncDict)