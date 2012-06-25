"""
File Name: S3Uploader.py
Purpose:
    Upload data to Amazon Web Services S3 buckets using BOTO, which is a library of classes and methods to work with Amazon AWS

File History:
    08-23-11 Alex Lee  Created

Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

import os
import boto
from boto.s3.key import Key as BotoKey

class S3Uploader(object):
    def __init__(self, bucketName, analyzerId):
        self.bucketName = bucketName
        self.analyzerId = analyzerId
        
    def upload(self, srcFilePath, tgtFilePath=None):
        try:
            s3Conn = boto.connect_s3()
            s3Bucket = s3Conn.get_bucket(self.bucketName)
        except:
            return {"error": "S3 connection issue - can't connect to bucket %s" % self.bucketName}
        
        try:
            fd = open(srcFilePath, 'rb')
            fileContents = fd.read()
            fd.close()
        except:
            return {"error": "File issue - can't read file %s" % srcFilePath}
    
        if s3Bucket:
            s3Key = BotoKey(s3Bucket)
            if not tgtFilePath:
                tgtFilePath = srcFilePath
            s3Key.key = "%s/%s" % (self.analyzerId, tgtFilePath)
            try:
                s3Key.set_contents_from_string(fileContents)
            except:
                return {"error": "S3 set error"}
        else:
            return {"error": "S3 bucket issue"}
            
        return "OK"

if __name__ == "__main__":

    # Example Usage   
        
    # The destination bucket should come from some configuration file.
    # The bucket boto config credentials must be authorized to "write" this bucket
    bucketName = 'picarro_analyzerup'

    # filePath should be the name of the H5 file to be uploaded
    logPath = "C:\Picarro\G2000\Log\DataLogger\DataLog_Private"
    filePath = os.path.join(logPath, [f for f in os.listdir(logPath) if f.endswith(".h5")][0])
    analyzerId = os.path.basename(filePath).split("-")[0]
    
    s3Uploader = S3Uploader(bucketName, analyzerId)
    print s3Uploader.upload(filePath)
    
    # filePath should be the name of the H5 file to be uploaded
    logPath = "C:\Picarro\G2000\Log\DataLogger\DataLog_User"
    filePath = os.path.join(logPath, [f for f in os.listdir(logPath) if f.endswith(".dat")][0])
    analyzerId = os.path.basename(filePath).split("-")[0]
    print s3Uploader.upload(filePath)
