"""
File Name: SupervisorAnalyzer.py
Purpose: Analyze the given supervisor INI file and generate an INI file for SpectrumMaker

File History:
    02-Apr-2015  Yuan       Initial version. The program can only analyse Fitter scripts that deal with single spectrumId. Program raise an error
                            if multiple spectrumId is found in Fitter script.
Copyright (c) 2015 Picarro, Inc. All rights reserved
"""

import sys
import getopt
import os
import re

from Host.Common.CustomConfigObj import CustomConfigObj
from Host.Fitter.fitterCoreWithFortran import *

DEFAULT_OUTPUT_FILENAME = "SpectrumMaker.ini"
FITTER_PATH = r"..\..\AppConfig\Config\Fitter"

class FitScript(object):
#extract spectral library, fit definition file and spectrumId from fit script
    def __init__(self, pyFile = ""):
        self.fileName = pyFile
        self.speclib=[]
        self.fitDef=[]
        if len(pyFile) > 0:
            self.analyze()

    def analyze(self):
    #Assume one FitScript object corresponding to one species. If multiple species are fitted in one fitScript, use config file for SupervisorAnalyzer
        pyFile = self.fileName
        if not os.path.exists(pyFile):
            raise Exception("Fit script '%s' not found" % pyFile)
        f = open(pyFile,'r')
        content = f.read()
        count = 0
        for line in content.splitlines():
            if "spectral library" in line and ".ini" in line:
                filePath = line.split("\"")[1]
                self.speclib.append(os.path.join(FITTER_PATH, filePath))
            elif "Analysis" in line and ".ini" in line:
                if line.strip().startswith("#"): continue
                filePath = line.split("\"")[1]
                self.fitDef.append(os.path.join(FITTER_PATH, filePath))
            elif "d[\"spectrumId\"]" in line and "in " in line:
                pattern = r'.*if\s+\(*d\["spectrumId"\]\s+in\s+\[((\d+,*\s*)+)\]\)*.*'
                if re.match(pattern, line) is not None:
                    self.spectrumId = re.sub(pattern, r'\1', line)
                    count += 1
            elif "d[\"spectrumId\"]" in line and "==" in line:
                pattern = r'.*if\s+\(*d\["spectrumId"\]\s*==\s*(\d+)\)*.*'
                if re.match(pattern, line) is not None:
                    self.spectrumId = re.sub(pattern, r'\1', line)
                    count += 1
            elif "species in" in line and "if" in line:
                pattern = r'.*if\s+\(*species\s+in\s+\[((\d+,*\s*)+)\]\)*.*'
                if re.match(pattern, line) is not None:
                    self.spectrumId = re.sub(pattern, r'\1', line)
                    count += 1
            elif "species" in line and "==" in line:
                pattern = r'.*if\s+\(*species\s*==\s*(\d+)\)*.*'
                if re.match(pattern, line) is not None:
                    self.spectrumId = re.sub(pattern, r'\1', line)
                    count += 1
        if count == 0:
            raise Exception("SpectrumID not found in %s" % pyFile)
        elif count > 1:
            raise Exception("Mupltiple spectrumId found in %s" % pyFile)
        f.close()

class SupervisorAnalyzer(object):
    def __init__(self, configFile, SupervisorConfigFile):
        if not os.path.exists(configFile):
            raise Exception("File '%s' not found" % configFile)
        if not os.path.exists(SupervisorConfigFile):
            raise Exception("File '%s' not found" % SupervisorConfigFile)
        basePath = os.path.dirname(SupervisorConfigFile)
        co = CustomConfigObj(SupervisorConfigFile)
        self.config = configFile
        self.fitScript = []
        self.SchemeCount = 0
        self.SchemePath = []
        if re.match(".+EXE.*", SupervisorConfigFile, re.I) is not None:
            self.SupervisorEXE = True
        else:
            self.SupervisorEXE = False
        FitScriptFromConfig = False
        if len(configFile) > 0: #extract fitScript info from config file
            co_analyzer = CustomConfigObj(configFile)
            for section in co_analyzer.list_sections():
                if section.startswith("FitScript"):
                    FitScriptFromConfig = True
                    fs = FitScript()
                    filePath = eval(co_analyzer.get(section, "spectral library"))
                    fs.speclib.append(os.path.join(FITTER_PATH, filePath))
                    filePath = eval(co_analyzer.get(section, "fit definition"))
                    fs.fitDef.append(os.path.join(FITTER_PATH, filePath))
                    fs.spectrumId = co_analyzer.get(section, "spectrumId")
                    self.fitScript.append(fs)

        if not FitScriptFromConfig:
            for appInfo in co["Applications"].items():
                if appInfo[0].startswith("Fitter"):
                    # find configuration file for fitter
                    FitterName = appInfo[0]
                    LaunchArgs = co.get(FitterName, "LaunchArgs")
                    FitterConfig = self._ExtractConfig(LaunchArgs)
                    # find fit scripts from config file of fitter
                    co_fitter = CustomConfigObj(FitterConfig)
                    for line in co_fitter["Setup"].items():
                        if line[0].startswith("Script"):
                            if "fitScriptLaserCurrentAverage" in line[1]:
                                continue
                            fs = os.path.join(basePath, line[1])
                            self.fitScript.append(FitScript(fs))

        # find measmode from instrument manager
        LaunchArgs = co.get("InstMgr", "LaunchArgs")
        InstMgrConfig = self._ExtractConfig(LaunchArgs)
        co_InstMgr = CustomConfigObj(InstMgrConfig)
        StartAppType = co_InstMgr.get("DEFAULT", "StartingAppType", "")
        if StartAppType in co_InstMgr.list_sections():
            MeasMode = co_InstMgr.get(StartAppType, "measmode")
        else:
            raise Exception("Measmode (%s) not found" % StartAppType)
        # find scheme file from measmode
        mode_path = "../../AppConfig/ModeInfo/"
        MeasModeFile = mode_path + MeasMode + ".mode"
        if not os.path.exists(MeasModeFile):
            raise Exception("ModeInfo file '%s' not found" % MeasModeFile)
        co_mode = CustomConfigObj(MeasModeFile)
        self.SchemeCount = co_mode.getint("SCHEME_CONFIG", "SchemeCount", 1)
        for line in co_mode["SCHEME_CONFIG"].items():
            if line[0].startswith("Scheme_"):
                self.SchemePath.append(mode_path + line[1])

    def _ExtractConfig(self, Input):
        try:
            switches, args = getopt.getopt(Input.split(), "vc:o:", "no_sample_mgr")
        except getopt.GetoptError, E:
            raise Exception("Unknown switches in %s" % Input)
        for o, a in switches:
            if o == "-c":
                if self.SupervisorEXE:
                    ConfigFile = "../" + a
                else:
                    ConfigFile = a
                if not os.path.exists(ConfigFile):
                    raise Exception("Config file not found: " + ConfigFile)
                else:
                    return ConfigFile

    def Output(self, fileName):
        co = open(fileName, 'w')
        config = CustomConfigObj(self.config)
        # CODE
        co.write("[CODE]\n")
        co.write("%s=%s\n" % ("code", r'"""'))
        co.write("from numpy import *\n")
        co.write("%s\n" % r'"""')
        # VARIABLES
        if config.has_section("VARIABLES"):
            co.write("[VARIABLES]\n")
            for name, value in config.list_items("VARIABLES"):
                co.write("%s=%s\n" % (name, value))
        # SCHEME_CONFIG
        co.write("[SCHEME_CONFIG]\n")
        co.write("SchemeCount=%d\n" % self.SchemeCount)
        for i in range(self.SchemeCount):
            co.write("Scheme_%d_Path=\"%s\"\n" % (i+1, self.SchemePath[i]))
        # SPECTRUM
        for i in range(len(self.fitScript)):
            fs = self.fitScript[i]
            co_fitDef = CustomConfigObj(fs.fitDef[0])
            section = "SPECTRUM_%d" % (i+1)
            co.write("[%s]\n" % section)
            co.write("SpectrumId=%s\n" % fs.spectrumId)
            co.write("Library=\"%s\"\n" % fs.speclib[0])
            try:
                center = co_fitDef.get("Region Fit Definitions", "center frequency")
                identification = co_fitDef.get("Region Fit Definitions", "peak identification")
            except KeyError:
                raise Exception("KeyError in %s\nFrom fitScript %s" % (fs.fitDef[0], fs.fileName))
            co.write("center=%s\n" % center)
            co.write("identification=%s\n" % identification)
            co.write("    [[base]]\n")
            co.write("    a0=base_array\n")
            for section in co_fitDef.list_sections():
                if section.startswith("function"):
                    co.write("    [[%s]]\n" % section)
                    for name, value in co_fitDef.list_items(section):
                        if "functional_form" in name:
                            co.write("    %s=\"%s\"\n" % (name, value))
                        else:
                            co.write("    %s=%s\n" % (name, value))
        print "Config file generated: %s" % fileName
        co.close()

HELP_STRING = """SupervisorAnalyzer.py [-c<FILENAME>] [-h|--help]

Where the options can be a combination of the following. Note that options override
settings in the configuration file:

-h, --help           print this help
-c                   specify config file: default = "SupervisorAnalyzer.ini"
-s                   specify config file of the supervisor: default = "../../AppConfig/Config/Supervisor/Supervisor.ini"
"""

def handleCommandSwitches():
    shortOpts = 'hc:s:'
    longOpts = ["help"]
    try:
        switches, args = getopt.getopt(sys.argv[1:], shortOpts, longOpts)
    except getopt.GetoptError, E:
        print "%s %r" % (E, E)
        sys.exit(1)
    #assemble a dictionary where the keys are the switches and values are switch args...
    options = {}
    for o,a in switches:
        options.setdefault(o,a)
    if "/?" in args or "/h" in args:
        options.setdefault('-h',"")
    #Start with option defaults...
    configFile = "SupervisorAnalyzer.ini"
    SupervisorConfigFile = "../../AppConfig/Config/Supervisor/Supervisor.ini"
    if "-h" in options or "--help" in options:
        printUsage()
        sys.exit()
    if "-c" in options:
        configFile = options["-c"]
    if "-s" in options:
        SupervisorConfigFile = options["-s"]
    return configFile, SupervisorConfigFile, options

if __name__ == "__main__":
    configFile, SupervisorConfigFile, options = handleCommandSwitches()
    SupervisorAnalyzerApp = SupervisorAnalyzer(configFile, SupervisorConfigFile)
    SupervisorAnalyzerApp.Output(DEFAULT_OUTPUT_FILENAME)