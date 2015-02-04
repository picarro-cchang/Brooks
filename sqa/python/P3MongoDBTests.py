#!/usr/bin/python

'''
Created on Jan 19, 2014

@author: zlu
'''

import subprocess

def main():
    
    rtn = subprocess.call('./P3MongoDBTest.py', shell = True)
    
    if rtn == 0:
        print "\nFinished running p3MongoDBTest.py\n"
    else:
        print "\nFinished running P3MongoDBTest.py but return code is not 0\n"
    
if __name__ == '__main__':
    main()
