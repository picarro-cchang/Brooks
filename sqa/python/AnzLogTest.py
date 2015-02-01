#!/usr/bin/python
'''
Created on Dec 21, 2013

@author: zlu
'''


from AnzLog import AnzLog
import P3RestAPITestHelper


def main():

    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzLog = AnzLog(**testProp)
    
    anzLog.get_byPos_alog_startPos0()
    
    anzLog.get_byPos_fnm_startPos0()
    
    anzLog.get_byEpoch_alog_startEtm0()
    
    anzLog.get_byEpoch_fnm_startEtm0()
    
    anzLog.get_byEpoch_anz_startEtm0()
    
    anzLog.get_resource()

if __name__ == '__main__':
    main()