#!/usr/bin/python
#
# File Name: ModeDef.py
# Purpose:
#   Contains all code for reading the various possible definitions for the
#   instrument modes.  This is used by, at least, MeasSys and DataManager.
#
# Notes:
#   It all starts from LoadModeDefinitions()
#
# ToDo:
#
# File History:
# 06-12-19 russ  First official release
# 07-10-23 sze   Added [INSTRUMENT_MODE] section to mode definition file
# 08-09-18  alex  Replaced SortedConfigParser with CustomConfigObj

import os
from CustomConfigObj import CustomConfigObj

class ModeDefException(Exception):
    "Base class for ModeDef exceptions"

class IllegalSection(ModeDefException): pass
class UnknownProcessorType(ModeDefException): pass
class ProcessorInvalid(ModeDefException): pass
class InvalidPath(ModeDefException): pass

PROCESSOR_TYPE_UNASSIGNED = -1
PROCESSOR_TYPE_FITTER = 0
PROCESSOR_TYPE_CALMGR = 1

SECTION_MODE_CONFIG= "ModeConfig"
SECTION_SYNC_ANALYSIS_CONFIG = "SYNC_SETUP"
OPTION_PROCESSOR_COUNT = "ProcessorCount"

def LoadModeDefinitions(ModeDefFilePath):
    """Loads mode info according to the def file.  Returns a dict of MeasMode.

    dict keys are the mode names.
    """
    if not os.path.exists(ModeDefFilePath):
        raise IOError("Base mode definition path not found: %s" % ModeDefFilePath)
    cp = CustomConfigObj(ModeDefFilePath) 
    defDir = os.path.split(ModeDefFilePath)[0]
    modeCount = cp.getint("AVAILABLE_MODES", "ModeCount")
    modeDict = {}
    baseDef = MeasMode()
    baseDef.ReadDefinition(ModeDefFilePath, ["AVAILABLE_MODES"], ["SCHEME_CONFIG"])
    for i in range(1, modeCount + 1):
        modeName = cp.get("AVAILABLE_MODES", "Mode_%d" % i)
        modePath = os.path.join(defDir, "%s.mode" % modeName)
        mode = baseDef.copy()
        mode.Name = modeName
        try:
            mode.ReadDefinition(modePath, IllegalSections = ["AVAILABLE_MODES"])
        except InvalidPath, excData:
            raise InvalidPath("Invalid path in '%s.mode' definition: '%s'" % (modeName, excData))
        modeDict[modeName] = mode
    return modeDict

class MeasMode(object):
    """

    self.Processors is a dictionary with a key per possible spectrum label. When
    a spectrum with a matching label arrives at the MeasSys, it will run all the
    labels in the processor list that is the dict value.

    self.Analyzers is a dictionary with a key per data label. When the
    DataManager sees a set of data with the matching label (either due to
    processor result being sent to it, or a data set with the label being
    generated) it will execute the indicated script.

    """
    def __init__(self):
        self.SourcePath = ""
        self.Name = ""
        self.SchemeCount = -1
        self.Schemes = [] # The list of schemes, in order, that the DAS should run in this mode

        self.SpectrumIdLookup = {} # Keys are spectrum IDs, values are names
        self.SyncSetup = []  #List of SyncAnalyzerInfo (what periodic scripts to run and how often)
        self.Processors = {} # Keys are spectrum names, values are lists of processors
        self.Analyzers = {}  # Dict of analyzers to match data labels

        self.SectionHandler = {}
        self.InstrumentModeDict = {}
        self._AssignSectionHandlers()

    def _AssignSectionHandlers(self):
        self.SectionHandler["INSTRUMENT_MODE"] = self._Read_INSTRUMENT_MODE
        self.SectionHandler["SCHEME_CONFIG"] = self._Read_SCHEME_CONFIG
        self.SectionHandler["SPECTRUM_IDS"] = self._Read_SPECTRUM_IDS
        self.SectionHandler["SYNC_SETUP"] = self._Read_SYNC_SETUP
        self.SectionHandler["SENSOR_DATA"] = self._Read_SENSOR_DATA

    def copy(self):
        "Returns a copy of this MeasMode instance."
        newCopy = MeasMode()
        newCopy.SpectrumIdLookup.update(self.SpectrumIdLookup)
        newCopy.SyncSetup = self.SyncSetup[:]
        newCopy.Processors.update(self.Processors)
        newCopy.Analyzers.update(self.Analyzers)
        newCopy.InstrumentModeDict.update(self.InstrumentModeDict)
        return newCopy

    def _Read_INSTRUMENT_MODE(self,cp,section):
        "Reads the instrument mode keys into a dictionary"
        self.InstrumentModeDict = {}
        for name,value in cp.list_items(section):
            self.InstrumentModeDict[name] = value

    def _GetInstrumentMode(self):
        return self.InstrumentModeDict

    def _Read_SCHEME_CONFIG(self, cp, section):
        basePath = os.path.split(self.SourcePath)[0]
        self.SchemeCount = cp.getint(section, "SchemeCount")
        for i in range(1, self.SchemeCount + 1):
            relPath = cp.get(section, "Scheme_%d_Path" % i)
            self.Schemes.append(os.path.abspath(os.path.join(basePath, relPath)))

    def _Read_SPECTRUM_IDS(self, cp, section):
        #Note: For some lame reason the string values in cp.items() normally come
        #back converted to lower case... this screws up several things later, so I
        #overrode the offending lower case conversion by changing
        #ConfigParser.optionxform at the time of loading.
        for item in cp.list_items(section):
            token = item[0]
            value = int(item[1])
            self.SpectrumIdLookup[value] = token

    def _Read_SYNC_SETUP(self, cp, section):
        basePath = os.path.split(self.SourcePath)[0]
        numSyncAnalyzers = cp.getint(section, "NumSyncAnalyzers")
        for i in range(numSyncAnalyzers):
            period_s = cp.getfloat(section, "Sync_%d_Period_s" % (i +1))
            reportName = cp.get(section, "Sync_%d_ReportName" % (i +1))
            scriptPath = os.path.join(basePath, cp.get(section, "Sync_%d_Script" % (i + 1)))
            try:
                scriptArgs = cp.get(section, "Sync_%d_ScriptArgs" % (i + 1)).split()
            except KeyError:
                scriptArgs = []
            analyzerInfo = AnalyzerInfo(scriptPath, scriptArgs)
            syncAnalyzerInfo = SyncAnalyzerInfo(period_s, reportName, analyzerInfo)
            self.SyncSetup.append(syncAnalyzerInfo)

    def _Read_SENSOR_DATA(self, cp, section):
        # the "SENSOR_DATA" label is a reserved name used when sensor data arrives
        # it can't have a processor!
        #tokens = [item[0] for item in cp.items(section)]
        #if ("FitInstructions" in tokens) or ("Processor_1_Type" in tokens):
        #  raise ProcessorInvalid("SENSOR_DATA cannot have a processor.")
        # NOTE - this checking is now managed for all cases in the generic
        #        _ReadDataLabelConfig
        self._ReadDataLabelConfig(cp, section)

    def _ReadDataLabelConfig(self, cp, Label):
        # In fact, anything that has a processor that is NOT a spectrum name is wrong
        basePath = os.path.split(self.SourcePath)[0]
        specialBasicFitterCase = False
        numProcessors = 0
        if Label != "SENSOR_DATA":
            if not cp.has_option(Label, OPTION_PROCESSOR_COUNT):
                numProcessors = 1
                specialBasicFitterCase = True
            else:
                numProcessors = cp.getint(Label, OPTION_PROCESSOR_COUNT)
        if specialBasicFitterCase:
            resultLabel = Label
            if cp.has_option(Label, "ResultLabel"):
                resultLabel = cp.get(Label, "ResultLabel")
            self.Processors[Label] = []
            self.Processors[Label].append(ProcessorInfo(PROCESSOR_TYPE_FITTER,resultLabel)),
        elif numProcessors > 0:
            self.Processors[Label] = []
            for i in range(1, numProcessors + 1):
                optPrefix = "Processor_%d" % i
                resultLabel = Label
                if cp.has_option(Label, optPrefix + "_ResultLabel"):
                    resultLabel = cp.get(Label, optPrefix + "_ResultLabel")
                processorType = cp.get(Label, optPrefix)
                if processorType.lower() == "fitter":
                    processorType = PROCESSOR_TYPE_FITTER
                elif processorType.lower() == "calmanager":
                    processorType = PROCESSOR_TYPE_CALMGR
                else:
                    raise UnknownProcessorType(processorType)
                if processorType == PROCESSOR_TYPE_FITTER:
                    self.Processors[Label].append(ProcessorInfo(PROCESSOR_TYPE_FITTER,resultLabel))
                elif processorType == PROCESSOR_TYPE_CALMGR:
                    self.Processors[Label].append(ProcessorInfo(PROCESSOR_TYPE_CALMGR, resultLabel))
                #endif
            #endfor (numProcessors)
        #endif (specialBasicFitterCase)
        if not cp.has_option(Label, "Analyzer"):
            self.Analyzers[Label] = None
        else:
            relPath = cp.get(Label, "Analyzer")
            if relPath.lower() == "none":
                self.Analyzers[Label] = None
            else:
                scriptPath = os.path.join(basePath, relPath)
                #Get the args, if any...
                if cp.has_option(Label, "Analyzer_Args"):
                    scriptArgs = cp.get(Label, "Analyzer_Args").split()
                else:
                    scriptArgs = []
                self.Analyzers[Label] = AnalyzerInfo(scriptPath, scriptArgs)

        if not self.Processors.has_key(Label) and not self.Analyzers.has_key(Label):
            raise IllegalSection("Section '%s' is not a valid section and must be fixed/removed!" % Label)

    def ReadDefinitionFP(self, fp, IgnoreSections = [], IllegalSections = []):
        cp = CustomConfigObj(fp, ignore_option_case=False) 
        #To stop the damn lower casing that ConfigParser does with optionxform -> OK....now it is taken care by CustomConfigObj!
        for section in cp.list_sections():
            if section in IgnoreSections:
                continue
            elif section in IllegalSections:
                raise IllegalSection
            elif section in self.SectionHandler.keys():
                self.SectionHandler[section](cp, section)
            else:
                #It is a section defining what to do for a data label...
                self._ReadDataLabelConfig(cp, section)
        #endfor
        #Sanity check the processors (should be for spectra only)...
        #print "Spectrum id:", self.SpectrumIdLookup.values()
        for label in self.Processors:
            if label not in self.SpectrumIdLookup.values():
                raise ProcessorInvalid("'%s' is not a spectrum name!  Processors are only for spectra, not generic data labels." % label)

    def ReadDefinition(self, FilePath, IgnoreSections = [], IllegalSections = []):
        fp = file(FilePath, "r")
        self.SourcePath = FilePath
        return self.ReadDefinitionFP(fp, IgnoreSections, IllegalSections)

class ProcessorInfo(object):
    def __init__(self,
                 Type,
                 ResultDataLabel):
        self.ProcessorType = Type
        self.ResultDataLabel = ResultDataLabel

class AnalyzerInfo(object):
    def __init__(self, ScriptPath, ScriptArgs):
        self.ScriptPath = ScriptPath
        self.ScriptArgs = ScriptArgs #A list of args (or an empty list if none)

class SyncAnalyzerInfo(object):
    def __init__(self, Period_s, ReportName, AnalyzerInfoObj):
        self.Period_s = Period_s
        self.ReportName = ReportName
        self.AnalyzerInfo = AnalyzerInfoObj
