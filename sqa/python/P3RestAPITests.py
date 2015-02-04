#!/usr/bin/python

'''
Created on Dec 21, 2013

@author: zlu
'''

import subprocess

import P3RestAPITestHelper

_testProp = "testProp"
_existing_tkt = "existing_tkt"
_doclist = "doclist"
_strTrue = "True"
_strFalse = "False"


def main():
    
    print "\nSetting '%s' to '%s' and '%s' to '%s'" % (_existing_tkt, _strFalse, _doclist, _strFalse)
    P3RestAPITestHelper.setProp(_testProp, _existing_tkt, _strFalse)
    P3RestAPITestHelper.setProp(_testProp, _doclist, _strFalse)
    runTests()
    
    print "\nSetting '%s' to '%s' and '%s' to '%s'" % (_existing_tkt, _strTrue, _doclist, _strFalse)
    P3RestAPITestHelper.setProp(_testProp, _existing_tkt, _strTrue)
    P3RestAPITestHelper.setProp(_testProp, _doclist, _strFalse)
    runTests()
    
    print "\nSetting '%s' to '%s' and '%s' to '%s'" % (_existing_tkt, _strFalse, _doclist, _strTrue)
    P3RestAPITestHelper.setProp(_testProp, _existing_tkt, _strFalse)
    P3RestAPITestHelper.setProp(_testProp, _doclist, _strTrue)
    runTests()            
    
    print "\nSetting '%s' to '%s' and '%s' to '%s'" % (_existing_tkt, _strTrue, _doclist, _strTrue)
    P3RestAPITestHelper.setProp(_testProp, _existing_tkt, _strTrue)
    P3RestAPITestHelper.setProp(_testProp, _doclist, _strTrue)
    runTests()
    
    summaryize()
    
    
def runTests():
    
    print '\n\nRunning AnzLogTest...\n'
    rtn = subprocess.call('./AnzLogTest.py', shell = True)
    if (rtn == 0):
        print '\nFinished running AnzLogTest with zero return code\n'
    else:
        print '\nFinished running AnzLogTest with a non-zero return code\n'    
    
    print '\n\nRunning AnzLogMetaTest...\n'
    rtn = subprocess.call('./AnzLogMetaTest.py', shell = True)
    if (rtn == 0):
        print '\nFinished running AnzLogMetaTest with return code 0\n'
    else:
        print '\nFinished running AnzLogMetaTest with a non-zero return code\n'
        
    print '\n\nRunning AnzMetaTest...\n'
    rtn = subprocess.call('./AnzMetaTest.py', shell = True)
    if (rtn == 0):
        print '\nFinished running AnzMetaTest with return code 0\n'
    else:
        print '\nFinished running AnzMetaTest with a non-zero return code\n'
        
    print "\n\nRunning AnzLrtTest...\n"
    rtn = subprocess.call('./AnzLrtTest.py', shell = True)
    if (rtn == 0):
        print "\nFinished running AnzLrtTest with return code 0\n"
    else:
        print "\nFinished running AnzLrtTest with a non-zero return code"
        
        
def summaryize():
    
    print "\n\n\nFinished running P3RestAPITests"            
        
        
if __name__ == '__main__':
    main()