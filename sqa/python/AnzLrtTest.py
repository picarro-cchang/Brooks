#!/usr/bin/python

'''
Created on Jan 30, 2014

@author: zlu
'''

from AnzLrt import AnzLrt
import P3RestAPITestHelper


def main():
    
    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzLrt = AnzLrt(**testProp)
    
    anzLrt.get_getStatus()
        
    anzLrt.get_byRow_startRow0()
        
    anzLrt.get_byRowFov_startRow0()
    
    
if __name__ == '__main__':
    main()