#!/usr/bin/python
'''
Created on Jan 22, 2014

@author: zlu
'''

from AnzLogMeta import AnzLogMeta
import P3RestAPITestHelper

def main():
    
    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzLogMeta = AnzLogMeta(**testProp)
    
    anzLogMeta.get_byEpoch_anz_startEtm0()
    
    anzLogMeta.get_byEpoch_alog_startEtm0()
    
    anzLogMeta.get_byEpoch_fnm_startEtm0()
    
    anzLogMeta.get_resource()
    
if __name__ == '__main__':
    main()