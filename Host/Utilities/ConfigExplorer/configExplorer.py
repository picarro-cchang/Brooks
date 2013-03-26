import os
import re
import configobj

def getMatches(fName,matchRe,matchOpt=re.I):
    f = None
    f = open(fName,'r')
    matches = []
    try:
        for str in f:
            if str.strip().startswith("#"): continue
            patt = re.compile(matchRe,matchOpt)
            matches += patt.findall(str)
        return matches
    finally:
        if f: f.close()

if __name__ == "__main__":
    baseName = r"C:\Picarro\G2000\AppConfig\Config\Supervisor\supervisorEXE_CFADS.ini"
    relName = '../AppConfig/Config/Fitter/Fitter1_CFADS.ini'
    basePath = r"C:\Picarro\G2000\HostExe"
    matchRe = r"\S*?\.ini|\S*?\.exe|\S*?\.py"
    print getMatches(os.path.join(basePath,relName),matchRe)

    baseName = r"C:\Picarro\G2000\AppConfig\Config\Supervisor\supervisorEXE_CFADS.ini"
    configObj = configobj.ConfigObj(baseName)
    print configObj.walk(lambda section,key: section[key])
    