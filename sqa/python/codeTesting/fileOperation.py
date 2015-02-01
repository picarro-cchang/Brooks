'''
Created on Feb 12, 2014

@author: zlu
'''


import shutil
import os


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
    setProp("testProp", "existing_tkt", "False")
    