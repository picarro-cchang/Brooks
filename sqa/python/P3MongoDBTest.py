#!/usr/bin/python

'''
Created on Jan 19, 2014

@author: zlu
'''

from P3MongoDB import P3MongoDB
import P3MongoDBHelper

def main():
    
    mDBProp = P3MongoDBHelper.getMDBProp()
    
    mongoDB = P3MongoDB(**mDBProp)
    
    mongoDB.findDuplicateRowsOnCollectionFNM()
    
    mongoDB.findDuplicateRowsOnAllCollectionsFNMs()
    
    mongoDB.checkLogsAndLogsListConsistency()

    mongoDB.checkExistenceConsistentcyOnCalculatedObjects()
        
    mongoDB.findInvalidObjectsInDatLogsCol()    

if __name__ == '__main__':
    main()