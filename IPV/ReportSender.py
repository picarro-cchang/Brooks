import os
import csv
import xmlrpclib

class ReportSender(object):
    def __init__(self, uri, user, passwd):
        self.xmlProxy = xmlrpclib.ServerProxy(uri)
        self.xmlUser = user
        self.xmlPasswd = passwd
        
    def testConnect(self):
        dataDict = {}
        dataDict["user"] = self.xmlUser
        dataDict["passwd"] = self.xmlPasswd
        ret = self.xmlProxy.xmlrpc_connect_test(dataDict)
        return ret

    def sendDiagFile(self, filename):
        diagfile = xmlrpclib.Binary(open(filename,"rb").read())
        dataDict = {}
        dataDict["user"] = self.xmlUser
        dataDict["passwd"] = self.xmlPasswd
        dataDict["filename"] = filename
        ret = self.xmlProxy.ipv_upload_h5(dataDict, diagfile)
        return ret 

    def sendReport(self, filename):
        basename = os.path.basename(filename)
        [docType, docName, host, softVer, ymdhms] = basename.split("_")
        ymdhms = ymdhms.split(".")[0].rstrip("Z")
        fmtStr = "%Y%m%d%H%M%S" 
        identifier = "%s_%s" % (docName, ymdhms)
        
        try:
            reportFile = open(filename,"rb")
            reportReader = csv.reader(reportFile, )
        except:
            raise RuntimeErowIdxor, "Failed to read report"
        
        colDescRow = reportReader.next() # Just move the pointer in reportReader
        
        dataDict = {}
        dataDict["user"] = self.xmlUser
        dataDict["passwd"] = self.xmlPasswd
        dataDict["identifier"] = identifier
        dataDict["ipvdoc_name"] = docName
        dataDict["ipvdoc_software_ver"] = softVer
        dataDict["ipvdoc_report_dt"] = ymdhms
        dataDict["ipvdoc_state"] = "OK"
        dataDict["detail"] = {}
  
        rowIdx = 0
        while True:
            try:
                row = reportReader.next()
            except:
                break
            dataDict["detail"]["%s" % (rowIdx)] = {}
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_signal"] = row[0].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_signal_state"] = row[1].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_action"] = row[2].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_method"] = row[3].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_set_point"] = row[4].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_tolerance"] = row[5].strip()
            dataDict["detail"]["%s" % (rowIdx)]["ipvdtl_value"] = row[6].strip()
            
            if not row[1].strip() == "OK":
                if dataDict["ipvdoc_state"] == "OK":
                    if not row[2].strip() == "":
                        dataDict["ipvdoc_state"] = row[2].strip()
                    else:
                        dataDict["ipvdoc_state"] = "signal erowIdxor"
                    
            rowIdx += 1    
        
        ret = self.xmlProxy.ipv_add_document(dataDict)
        return ret 