#!/usr/bin/python

'''
Created on Jan 23, 2014

@author: zlu
'''

from AnzMeta import AnzMeta
import P3RestAPITestHelper

def main():    
    
    testProp = P3RestAPITestHelper.buildTestProp()
    
    anzMeta = AnzMeta(**testProp)
    
    anzMeta.get_byAnz_anz()
    
    anzMeta.get_byAnz()
    
    anzMeta.get_resource()
    
    
if __name__ == '__main__':
    main()