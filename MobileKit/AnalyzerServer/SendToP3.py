'''
SendToP3.py - Spawns DatEchoP3 to send a collection of files to P3
'''
from glob import glob
import os
import re
import sys
import subprocess

from Host.Common.configobj import ConfigObj

VER = "1.0"
if hasattr(sys, "frozen"): #we're running compiled with py2exe
    AppPath = sys.executable
else:
    AppPath = sys.argv[0]

if __name__ == "__main__":
    callParams = []
    nlines = 1000
    # The configuration filename is the same as the executable, except that it has an 
    #  extension of .ini
    basePath = os.path.split(AppPath)[0]
    configFile = os.path.splitext(AppPath)[0] + ".ini"
    config = ConfigObj(configFile)
    params = config["SENDTOP3"]
    # Here are the regular expressions for various data types
    typeRegex = {"dat" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.dat)$"""),
                 "peaks" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.peaks)$"""),
                 "analysis" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_User_Minimal\.peaks)$"""),
                 "GPS_Raw" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_GPS_Raw\.dat)$"""),
                 "WS_Raw" : re.compile(r"""(?i)^(.*?)-(.*?)-(.*?)-(DataLog_WS_Raw\.dat)$""")}
    
    # Prepare command to call the DatEchoP3 worker, which may be a Python file or 
    #  an executable
    worker = os.path.join(basePath,params["worker"])
    if os.path.splitext(worker)[-1].lower() == ".py":
        callParams.append("python")
    callParams.append(worker)
    # Make up the arguments for DatEchoP3
    baseUrl = params["baseurl"]
    csp = params["csp"]
    ticketUrl = "https://" + "/".join([baseUrl,csp,"rest","sec","dummy",VER,"Admin"])
    ipReqUrl = "https://" + "/".join([baseUrl,csp,"rest","gdu","<TICKET>",VER,"AnzMeta"])
    pushUrl  = "https://" + "/".join([baseUrl,csp,"rest","gdu","<TICKET>",VER,"AnzLog"])
    psys = params["sys"]
    identity = params["identity"]
    files = params["files"]
    callParams.append("--ticket-url")
    callParams.append(ticketUrl)
    callParams.append("--ip-req-url")
    callParams.append(ipReqUrl)
    callParams.append("--push-url")
    callParams.append(pushUrl)
    callParams.append("--sys")
    callParams.append(psys)    
    callParams.append("--identity")
    callParams.append(identity)
    callParams.append("--nbr-lines")
    callParams.append("%s" % nlines)
    callParams.append("--replace")
    for f in glob(files):
        fParams = ["--file-path"]
        fParams.append(f)
        # Determine the data type
        for dt in typeRegex:
            if typeRegex[dt].search(f):
                fParams.append("--data-type")
                fParams.append(dt)
                subprocess.call(callParams + fParams)
                break
        else:
            print "%s does not match name of known file types" % f
            