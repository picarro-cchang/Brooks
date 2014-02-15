#!/usr/bin/python

'''
Created on Dec 20, 2013

@author: zlu
'''


import shutil
import os


def buildTestProp():
    testProp_dict = {}
    
    f = open("testProp", "r")

    for line in f:
        if line.strip() != '' and line[0] != "#":
            propList = line.split("=")
            testProp_dict[propList[0].strip()] = propList[1].strip()
            
    for key in testProp_dict.keys():
        if testProp_dict[key] == "True":
            testProp_dict.pop(key)
            testProp_dict[key] = True
        elif testProp_dict[key] == "False":
            testProp_dict.pop(key)
            testProp_dict[key] = False
        
    f.close()

    return testProp_dict


def setProp(testProp, strKey, strValue):
        
    strProp = ""
    
    try:
        
        f = open(testProp, "r")
         
        for line in f:
            if line.strip() == '':
                strProp += "\n"
            elif strKey in line:
                strProp += strKey + " = " + strValue + "\n"
            else:
                strProp += line
                 
        f.close()
        
        ftemp = open("tempFile", "w")
        
        ftemp.write(strProp)
        
        ftemp.close()
        
        os.remove(testProp)
        
        shutil.move("tempFile", testProp)
            
    except Exception, e:
        
        print "\nException (Error): ", str(e)
        

if __name__ == '__main__':
      
    testProp_dict = buildTestProp()
    
    print testProp_dict
    
    for key in testProp_dict.keys():
        if type(testProp_dict[key]) == bool:
                testProp_dict[key] = str(testProp_dict[key])
        print key + " = " + testProp_dict[key]

