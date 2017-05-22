"""
This module is to help pyBuilder communicating with unittest modules.
When building installers, pyBuilder writes build information
into BuildInfo.py in this folder.
"""
import time

def isAnalyzerToBuild(analyzerTypeList):
    # return True if one type in analyzerTypeList matches buildTypes of PyBuilder
    try:
        from Host.Utilities.BuildHelper.BuildInfo import buildTime, buildTypes
        if time.time() - buildTime < 13600:
            for t in analyzerTypeList:
                if t in buildTypes:
                    return True
        return False
    except:
        return False

def getBuildFolder():
    try:
        from Host.Utilities.BuildHelper.BuildInfo import buildTime, buildFolder
        if time.time() - buildTime < 13600:
            return buildFolder
        return ""
    except:
        return ""