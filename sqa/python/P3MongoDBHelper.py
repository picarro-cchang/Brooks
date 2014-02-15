'''
Created on Jan 17, 2014

@author: zlu
'''

import configobj

def getMDBProp():
    
    config  = configobj.ConfigObj("P3MongoDBProp")
    
    for key in config:
        if config[key] == 'True':
            config[key] = True
        
        if config[key] == 'False':
            config[key] = False
    
    return config

if __name__ == '__main__':  
    
    mDBProp = getMDBProp()
        
    print "\nThe prop list is: ", mDBProp
    
    for key in mDBProp.keys():
        if type(mDBProp[key]) == bool:
                mDBProp[key] = str(mDBProp[key])
        print "\n" + key + " = " + mDBProp[key]
