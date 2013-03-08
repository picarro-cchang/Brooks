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

MAX_CACHED_FILES = 32
cachedFiles = OrderedDict()

def getSlice(filename,start=None,end=None,clear=False):
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
    return cachedFiles[filename].getSlice(start,end)
        
class LineCachedFile(object):
    def __init__(self,filename):
        self.linePtr = [0]
        self.filename = os.path.abspath(filename)
        
    def getSlice(self,start=None,end=None):
        if os.path.getsize(self.filename) == 0: return []
        with open(self.filename,"rb") as f:
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
            for p in self.linePtr[start:end]:
                # If we do not see expected newlines, flush cache and try again
                if p>0 and fmap[p-1] != "\n":
                    print "ERROR: Lines changed in file!"
                    self.clear()
                    return self.getSlice(start,end)
                result.append(getLine(p))
            fmap.close()
        return result
    
    def clear(self):
        self.linePtr = [0]

# Simple test code
        
if __name__ == "__main__":
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode="wb",delete=False) as f:
        fname = f.name
        pass
    assert getSlice(fname,0,10) == []
    assert getSlice(fname,0) == []
    
    with open(fname,"wb") as f:
        f.write("\n\n ")
    assert getSlice(fname,0,10,clear=True) == ["\n", "\n", " "]
    assert getSlice(fname,0,-1) == ["\n", "\n"]

    with open(fname,"wb") as f:
        f.write("First line\nNo newline at EOF")
    assert getSlice(fname,0,10,clear=True) == ["First line\n", "No newline at EOF"]
    
    with open(fname,"wb") as f:
        f.write("First line\nWith newline at EOF\n")
    assert getSlice(fname,0,10,clear=True) == ["First line\n", "With newline at EOF\n"]

    with tempfile.NamedTemporaryFile(mode="wb",delete=False) as f:
        fname1 = f.name
        for i in range(20000):
            print >>f, "This is line %d" % i
    assert getSlice(fname1,None,10) == [("This is line %d\n" % i) for i in range(10)]
    assert getSlice(fname1,-10,None)  == [("This is line %d\n" % i) for i in range(20000-10,20000)]
    assert getSlice(fname1,17,54)  == [("This is line %d\n" % i) for i in range(17,54)]
    assert getSlice(fname1,1000,-1000)  == [("This is line %d\n" % i) for i in range(1000,20000-1000)]
    
    os.unlink(fname)
    os.unlink(fname1)