#!/usr/bin/python
#
"""
File Name: LineCacheMmap.py
Purpose: Uses memory mapping to support line-based access to text files.
 
 It provides the following function:
  
  getSlice(filename,start=None,end=None,clear=False)
    Returns lines from start to end (using Python 0-origin slice semantics) from the specified filename.
     A cache is maintained which maps line numbers to byte offsets in the file. This cache is lazily
     evaluated as requests are made. If the file is changed by some other application while it is cached
     the cache entry for the file must be cleared before extracting the slice by setting clear=True.
    The cached filenames are stored in an ordered dictionary so that the least recently used file
     can be released if there are too many (>MAX_CACHED_FILES) mappings.
 
 A new mmap is created for each slice request, so that this works with a dynamically growing file. 
  Access to the file is read-only.

File History:
 17-Dec-2011  sze    Initial version
    
 Copyright (c) 2011 Picarro, Inc. All rights reserved
"""

from Host.Common.ordereddict import OrderedDict
import mmap
import os
from Host.Common.namedtuple import namedtuple

MAX_CACHED_FILES = 32
cachedFiles = OrderedDict()
NumberedLine = namedtuple('NumberedLine','lineNumber line')

def getSliceIter(filename,start=None,end=None,clear=False):
    filename = os.path.abspath(filename)
    if filename in cachedFiles:
        # Move to front and return cached file
        c = cachedFiles[filename]
        del cachedFiles[filename]
        cachedFiles[filename] = c
    else:
        cachedFiles[filename] = LineCachedFile(filename)
        # Remove least recently used, if too many files cached
        if len(cachedFiles) > MAX_CACHED_FILES:
            cachedFiles.popitem(last=False).clear()
    if clear: cachedFiles[filename].clear()
    for l in cachedFiles[filename].getSliceIter(start,end): yield l
    
def getSlice(filename,start=None,end=None,clear=False):
    return [l for l in getSliceIter(filename,start,end,clear)]

class LineCachedFile(object):
    def __init__(self,filename):
        self.linePtr = [0]
        self.filename = os.path.abspath(filename)
        
    def getSliceIter(self,start=None,end=None):
        if os.path.getsize(self.filename) == 0: return
        try:
            f = open(self.filename,"rb")
            fmap = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
            def getLine(p):
                fmap.seek(p)
                return fmap.readline()
            sol = self.linePtr[-1]
            eol = fmap.find("\n",sol)
            while  eol>= 0:
                sol = eol+1
                if sol>=len(fmap) or (end>=0 and len(self.linePtr)>=end): break
                self.linePtr.append(sol)
                eol = fmap.find("\n",sol)
            result = []
            # Assemble the slice by reading lines starting at locations in fmap
            if start is None: start = 0
            elif start<0: start=max(0,start+len(self.linePtr))
            for i,p in enumerate(self.linePtr[start:end]):
                # If we do not see expected newlines, this is an error
                if p>0 and fmap[p-1] != "\n":
                    raise RuntimeError("Lines changed in cached file!")
                yield NumberedLine(start+i,getLine(p))
            fmap.close()
        finally:
            f.close()
    
    def clear(self):
        self.linePtr = [0]

# Simple test code
        
if __name__ == "__main__":
    import tempfile
    
    try:
        f = open("tempFile.tmp",mode="wb")
        fname = f.name
        pass
    finally:
        f.close()
    assert getSlice(fname,0,10) == []
    assert getSlice(fname,0) == []
    
    try:
        f = open(fname,"wb")
        f.write("\n\n ")
    finally:
        f.close()
    assert getSlice(fname,0,10,clear=True) == [(0,"\n"), (1,"\n"), (2," ")]
    assert getSlice(fname,0,-1) == [(0,"\n"), (1,"\n")]

    try:
        f = open(fname,"wb")
        f.write("First line\nNo newline at EOF")
    finally:
        f.close()
    assert getSlice(fname,0,10,clear=True) == [(0,"First line\n"), (1,"No newline at EOF")]
    
    try:
        f = open(fname,"wb")
        f.write("First line\nWith newline at EOF\n")
    finally:
        f.close()
    assert getSlice(fname,0,10,clear=True) == [(0,"First line\n"), (1,"With newline at EOF\n")]

    try:
        f = open("tempFile1.tmp",mode="wb")
        fname1 = f.name
        for i in range(20000):
            print >>f, "This is line %d" % i
    finally:
        f.close()
    assert getSlice(fname1,None,10) == [(i,"This is line %d\n" % i) for i in range(10)]
    assert getSlice(fname1,-10,None)  == [(i,"This is line %d\n" % i) for i in range(20000-10,20000)]
    assert getSlice(fname1,17,54)  == [(i,"This is line %d\n" % i) for i in range(17,54)]
    assert getSlice(fname1,1000,-1000)  == [(i,"This is line %d\n" % i) for i in range(1000,20000-1000)]
    assert getSlice(fname1,-30000,10)  == [(i,"This is line %d\n" % i) for i in range(0,10)]
    
    os.unlink(fname)
    os.unlink(fname1)