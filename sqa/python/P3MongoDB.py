'''
Created on Jan 17, 2014

@author: zlu
'''

import pymongo
import P3MongoDBHelper
import re

class P3MongoDB():
    def __init__(self, *args, **kvargs):
        #=======================================================================
        # self.mCollections = ["analyzer", "analyzer_analysis_logs", "analyzer_analysis_logs_list", "analyzer_dat_logs", "analyzer_dat_logs_list",
        #                      "analyzer_fov_logs", "analyzer_fov_logs_list", "analyzer_log_notes", "analyzer_peak_logs", "analyzer_peak_logs_list", 
        #                      "counters", "fov_xxxx", "generic_dat_logs", "generic_dat_logs_list", "immutable_names", "lrt_xxxx", "lrt_meta", 
        #                      "process_status", "system.indexes"]
        #=======================================================================
        
        self.anzDatLogsListColName = "analyzer_dat_logs_list"
        self.anzDatLogsColName = "analyzer_dat_logs"
        
        self.logsPairDict = {}
        self.logsPairDict["analyzer_analysis_logs"] = "analyzer_analysis_logs_list"
        self.logsPairDict["analyzer_dat_logs"] = "analyzer_dat_logs_list"
        self.logsPairDict["analyzer_fov_logs"] = "analyzer_fov_logs_list"
        self.logsPairDict["analyzer_peak_logs"] = "analyzer_peak_logs_list"
        
        self.logsListColNames = ["analyzer_peak_logs_list", "analyzer_analysis_logs_list"] #not including fov, will check with Sze about fov pair
        
        #=======================================================================
        # #Testing list
        # self.logsPairDict = {}
        # self.logsPairDict["analyzer_analysis_logs"] = "analyzer_analysis_logs_list"
        # self.logsPairDict["analyzer_dat_logs"] = "analyzer_analysis_logs_list"
        # self.logsPairDict["analyzer_fov_logs"] = "analyzer_fov_logs_list"
        # self.logsPairDict["analyzer_peak_logs"] = "analyzer_fov_logs_list"        
        #=======================================================================
        
        self.host = None
        if 'host' in kvargs:
            self.host = kvargs['host']
            
        self.port = None
        if 'port' in kvargs:
            self.port = int(kvargs['port'])
        
        self.dbName = None
        if 'dbName' in kvargs:
            self.dbName = kvargs['dbName']
        
        self.debug = None
        if 'debug' in kvargs:
            self.debug = kvargs['debug']
        
        self.collectionName = None
        if 'collectionName' in kvargs:
            self.collectionName = kvargs['collectionName']
        
        self.fnm = None
        if 'fnm' in kvargs:
            self.fnm = int(kvargs['fnm'])
        
        self.mClient = self._makeConnection()        
        self.mDB = self.mClient[self.dbName]
        self.mCollection = self.mDB[self.collectionName] 

        if (self.debug):
            print "\nself.host = %s, self.port = %d, self.dbName = %s, self.mCollection = %s" % (self.host, self.port, self.dbName, self.mCollection.name)

    def _makeConnection(self):
        try:
            return pymongo.MongoClient(self.host, self.port)
        except:
            print '\nFailed to connect to mongo db'
            exit(1)
    
    def findDuplicateRowsOnCollectionFNM(self, mColName = None, fnm = None):
 
        if mColName is None:
            mCol = self.mCollection
        else:
            mCol = self.mDB[mColName]
            
        if fnm is None:
            fnm = self.fnm
            
        print "\n\n\n...Finding duplicate rows on %s with fnm = %d..." % (mCol.name, fnm)
        
        docs = mCol.find({'fnm': fnm})
        
        aList = []
        
        try:
            aList = [doc['row'] for doc in docs]    
        except KeyError:
            print "No row field in collection %s with fnm %d" % (mCol.name, fnm) #check with Sze: there is only a string row field in the "docmap" in logsList
            
        uniqueList = set(aList)
        
        if (self.debug):
            print "For %s: the length of uniqueList is %d and the length of aList is %d" % (mCol.name, len(uniqueList), len(aList))
      
        if len(uniqueList) < len(aList):
            self._showDuplicateRowNumsOnCollectionFNM(mCol, fnm)
        else:
            print '\nNo duplicate rows found on %s.%s with fnm = %s' % (self.dbName, mCol.name, fnm) 
            
    def findDuplicateRowsOnAllCollectionsFNMs(self):
        
        print "\n\n\n...Finding duplicate rows on all collections by fnms..."
        
        collectionNames = self.mClient[self.dbName].collection_names()
        if (self.debug):
            print "\nThe collection names in %s db are: " % (self.dbName), collectionNames
        
        collectionList = [self.mClient[self.dbName][name] for name in collectionNames]
        
        fnmList = []    
            
        for mCol in collectionList:
            docs = mCol.find()
            
            fnmList = set([doc['fnm'] for doc in docs if 'fnm' in doc])
            
            if (self.debug):                
                print "\nFor collection %s " % (mCol.name) + ", the unique sorted fnmList is: ", sorted(fnmList)
            
            for fnm in fnmList:
                self.findDuplicateRowsOnCollectionFNM(mCol.name, fnm)
                
            fnmList.clear()  
                                
    def _showDuplicateRowNumsOnCollectionFNM(self, mCol, fnm):
        docs = mCol.find({'fnm': fnm})
        uniqueList = set()
        dupList = set()
        
        for doc in docs:
            row = doc["row"]
            if (row in uniqueList):
                dupList.add(row)
            else:
                uniqueList.add(row)
                
        if (len(dupList) > 0):
            print "\nThere are duplicated rows in %s.%s for 'fnm' %s and the following are the duplicate row numbers" % (self.dbName, mCol.name, fnm)
            print "The duplicated row list is: ", dupList
        
    def _getFNMSetFromCollection(self, mColName):
        
        mCol = self.mDB[mColName]
        
        docs = mCol.find()
        
        fnmList = set(doc["fnm"] for doc in docs if 'fnm' in doc)
        
        if (self.debug):
            print "\nfnm set for %s is: " % (mColName), fnmList
            print "\nfnm set size for %s is: %d" % (mColName, len(fnmList))
        
        if fnmList:
            return fnmList
    
    def checkLogsAndLogsListConsistency(self):
        
        print "\n\n\n...Checking logs are consistent with Logs List..."
        
        rtnFlag = True
        
        for key in self.logsPairDict:
            try:
                assert (self._getFNMSetFromCollection(key) == self._getFNMSetFromCollection(self.logsPairDict[key]))
            except AssertionError:
                print "\nFailed equal assertion on fnm set for %s and %s\n" % (key, self.logsPairDict[key])
                rtnFlag = False
            
        return rtnFlag
        
    def _getLogNameList(self, colName):
        mCol = self.mDB[colName]
        docs = mCol.find()
        
        logNameList = set(doc['logname'] for doc in docs if 'logname' in doc)
        
        return logNameList

    def checkExistenceConsistentcyOnCalculatedObjects(self):
        
        print "\n\n\n...Checking existence consistency on calculated objects from analyzer_dat_logs_list..."
        
        anzDatLogsListCol = self.mDB[self.anzDatLogsListColName]
        
        rtnFlag = True
        
        for colName in self.logsListColNames:
            logNameList = self._getLogNameList(colName)
       
            for logName in logNameList:
                strList = logName.split(".")
                baseLogName = strList[0]
                logNameType = strList[1]
                
                regex = re.compile(baseLogName)
                
                count = anzDatLogsListCol.find({'logname': regex}).count()
                
                if (count == 0):
                    print "\nThere is no corresponding dat log in %s so %s in %s is invalid" % (self.anzDatLogsListColName, logName, colName) 
                    self._findInvalidObjecsInLogsCol(colName, logName)
                    rtnFlag = False
                elif (self.debug):
                    print "\nThere is corresponding dat log in %s for %s in %s" % (self.anzDatLogsListColName, logName, colName)
                    
        return rtnFlag 

    def _findInvalidObjecsInLogsCol(self, colName, logName):
        mCol = self.mDB[colName]
        docs = mCol.find()
        
        fnm = None
        
        for doc in docs:
            if doc['logname'] == logName:
                fnm = doc['fnm']
                break 
        
        datLogsColName = ""
            
        inverseLogsPairDict = {v: k for k, v in self.logsPairDict.items()}
        
        for key in inverseLogsPairDict:
            if key == colName:
                datLogsColName = inverseLogsPairDict[key]
                break
         
        print "Finding invalid objects in %s with fnm = %d..." % (datLogsColName, fnm) 
         
        datLogsCol = self.mDB[datLogsColName]
        docs = datLogsCol.find({'fnm':fnm})
        
        if (docs):
            print "There are %d objects with fnm = %d invalid in %s" % (docs.count(), fnm, datLogsColName)
            
    def findInvalidObjectsInDatLogsCol(self):
        
        print "\n\n\n...Finding invalid objects in Analyzer_dat_logs..."

        anzDatLogsListFNMSet = self._getFNMSetFromCollection(self.anzDatLogsListColName)
        
        anzDatLogsFNMSet = self._getFNMSetFromCollection(self.anzDatLogsColName)
        
        invalidFNMList = set()
        
        if anzDatLogsFNMSet != anzDatLogsListFNMSet:
            for fnm in anzDatLogsFNMSet:
                if fnm not in anzDatLogsListFNMSet:
                    invalidFNMList.add(fnm)
                    print "\nThere is(are) invalid object(s) in %s with fnm = %d" % (self.anzDatLogsColName, fnm)
        else:
            print "\nDidn't find any invalid objects in %s" % (self.anzDatLogsColName)
        
        if len(invalidFNMList) > 0:
            print "\nThe invalid fnm list for %s is: " % (self.anzDatLogsColName), invalidFNMList
            
        return invalidFNMList
                                               
    def __def__(self):
        if (self.mongoClient):
            self.mongoClient.close()

if __name__ == '__main__':
    mDBProp = P3MongoDBHelper.getMDBProp()
    
    mongoDB = P3MongoDB(**mDBProp)
    
    mongoDB.findDuplicateRowsOnCollectionFNM()
    
    mongoDB.findDuplicateRowsOnAllCollectionsFNMs()
    
    mongoDB.checkLogsAndLogsListConsistency()

    mongoDB.checkExistenceConsistentcyOnCalculatedObjects()
        
    mongoDB.findInvalidObjectsInDatLogsCol()