"""
This module is to help pyBuilder communicating with unittest modules.
When building installers, pyBuilder writes analyzer types to be built
into BuildTypes.py in this folder.
"""
import time

def isAnalyzerToBuild(analyzerTypeList):
    # return True if one type in analyzerTypeList matches buildTypes of PyBuilder
    try:
        from Host.Utilities.BuildHelper.BuildTypes import buildTime, buildTypes
        if time.time() - buildTime < 3600:
            for t in analyzerTypeList:
                if t in buildTypes:
                    return True
        return False
    except:
        return False