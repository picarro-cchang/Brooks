'''
Hdf5toMat.py: Conversion program for simple HDF5 files to Matlab MAT files

Created on Apr 10, 2010

@author: Sze Tan
'''

import numpy as np
import sys
import struct
from tables import openFile, Table

# MAT-file data types
miINT8    = 1
miUINT8   = 2
miINT16   = 3
miUINT16  = 4
miINT32   = 5
miUINT32  = 6
miSINGLE  = 7
miDOUBLE  = 9
miINT64   = 12
miUINT64  = 13
miMATRIX  = 14

# MATLAB Array types
mxCELL_CLASS   = 1
mxSTRUCT_CLASS = 2
mxOBJECT_CLASS = 3
mxCHAR_CLASS   = 4
mxSPARSE_CLASS = 5
mxDOUBLE_CLASS = 6
mxSINGLE_CLASS = 7
mxINT8CLASS    = 8
mxUINT8CLASS   = 9
mxINT16CLASS   = 10
mxUINT16CLASS  = 11
mxINT32_CLASS  = 12
mxUINT32_CLASS = 13

# Bit masks for array flags
mfLOGICAL = 2
mfGLOBAL  = 4
mfCOMPLEX = 8

class Hdf5ToMat(object):
    '''
    Converts an HDF5 containing real-valued tables into a Matlab MAT file.
    The tables in the HDF5 file are mapped to Matlab structures. The columns
    of each table map to array-valued fields.   
    '''

    def __init__(self,h5FileName,matFileName):
        '''
        Constructor in which the input HDF5 file and the output MAT file are 
        specified
        '''
        self.h5FileName,self.matFileName = h5FileName,matFileName
        self.h5 = openFile(h5FileName, "r")
        self.mat = file(matFileName, "wb")
        
    def headerAsString(self,description,version=0x0100,endian="IM"):
        '''
        Write the MAT header which consists of a 124 byte text description
        followed by the version and an endian indicator
        '''
        descr = description[:124]
        descr += (124-len(descr)) * ' '
        return struct.pack("=124sH2s",descr,version,endian)
    
    def structureAsString(self,name,npRecordArray):
        '''Write out a numpy record array'''
        structStringList = []
        # Array flags
        structStringList.append(struct.pack("=IIBxxxxxxx",miUINT32,8,mxSTRUCT_CLASS))
        # Structure array has only one element
        structStringList.append(struct.pack("=IIII",miINT32,8,1,1))
        # This is followed by the name    
        structStringList.append(struct.pack("=II",miINT8,len(name)))
        structStringList.append(struct.pack("=%ds" % len(name),name))
        if len(name) & 7:
            pad = 8 - (len(name) & 7)
            structStringList.append(struct.pack(pad*"x"))
        # Next is the maximum length of the field names
        structStringList.append(struct.pack("=HHI",miINT32,4,32))
        # Followed by the field names, each padded to length 32        
        names = npRecordArray.dtype.names
        structStringList.append(struct.pack("=II",miINT8,32*len(names)))
        for name in names:
            structStringList.append(struct.pack("=32s",name[:31]))
        # Append matrices in the structure
        for name in names:
            structStringList.append(self.matrixAsString("",npRecordArray[name]))
        structString = "".join(structStringList)
        return struct.pack("=II",miMATRIX,len(structString)) + structString
            
    def matrixAsString(self,name,npArray):
        '''Write out a numpy array'''
        npArray = np.asarray(npArray,dtype=np.double)
        matrixStringList = []
        # Array flags
        flags = 0
        matrixStringList.append(struct.pack("=IIBBxxxxxx",miUINT32,8,mxDOUBLE_CLASS,flags))
        # Next specify the dimensions
        shape = npArray.shape
        ndims = len(shape)
        if ndims == 1:
            shape = shape + (1,)
            ndims += 1
        matrixStringList.append(struct.pack("=II",miINT32,4*ndims))
        matrixStringList.append(struct.pack("=" + ndims*"I",*shape))
        if ndims & 1:
            matrixStringList.append(struct.pack("xxxx"))
        # This is followed by the name    
        matrixStringList.append(struct.pack("=II",miINT8,len(name)))
        if name:
            matrixStringList.append(struct.pack("=%ds" % len(name),name))
            if len(name) & 7:
                pad = 8 - (len(name) & 7)
                matrixStringList.append(struct.pack(pad*"x"))
        # The actual data follow
        arrayString = npArray.tostring(order='F')
        matrixStringList.append(struct.pack("=II",miDOUBLE,len(arrayString)))
        matrixStringList.append(arrayString)
        if len(arrayString) & 7:
            pad = 8 - (len(arrayString) & 7)
            matrixStringList.append(struct.pack(pad*"x"))
        matrixString = "".join(matrixStringList)
        return struct.pack("=II",miMATRIX,len(matrixString)) + matrixString
    
    def writeMat(self):
        self.mat.write(self.headerAsString("MATLAB 5.0 MAT-file, Converted by Hdf5ToMat from %s" % self.h5FileName))
        tableNames = []
        for n in self.h5.walkNodes("/"):
            if isinstance(n,Table):
                tableNames.append(n._v_pathname)
        for name in tableNames:
            table = self.h5.getNode(name)
            self.mat.write(self.structureAsString(name[1:].replace("/","_"),table.read()))
        self.h5.close()
        self.mat.close()
        
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage: %s h5_file mat_file\nConverts HDF5 file to Matlab MAT file" % sys.argv[0]
    else:
        h = Hdf5ToMat(sys.argv[1],sys.argv[2])
        h.writeMat()
    