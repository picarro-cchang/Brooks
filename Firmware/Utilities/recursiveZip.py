# Recursively unzip files in this directory and all subdirectories

import os
from zipfile import ZipFile

def sortByName(top,nameList):
    nameList.sort()
    return nameList

def sortByMtime(top,nameList):
    """Sort a list of files by modification time"""
    # Decorate with the modification time of the file for sorting
    fileList = [(os.path.getmtime(os.path.join(top,name)),name) for name in nameList]
    fileList.sort()
    return [name for t,name in fileList]
    
def walkTree(top,onError=None,sortDir=None,sortFiles=None):
    """Generator which traverses a directory tree rooted at "top" in bottom to top order (i.e., the children are visited
    before the parent, and directories are visited before files.) The order of directory traversal is determined by
    "sortDir" and the order of file traversal is determined by "sortFiles". If "onError" is defined, exceptions during
    directory listings are passed to this function. When the function yields a result, it is either the pair
    ('file',fileName)  or ('dir',directoryName)"""
    try:
        names = os.listdir(top)
    except OSError, err:
        if onError is not None:
            onError(err)
        return
    # Obtain lists of directories and files which are not links
    dirs, nondirs = [], []
    for name in names:
        fullName = os.path.join(top,name)
        if not os.path.islink(fullName):
            if os.path.isdir(fullName):
                dirs.append(name)
            else:
                nondirs.append(name)
    # Sort the directories and nondirectories (in-place)
    if sortDir is not None:
        dirs = sortDir(top,dirs)
    if sortFiles is not None:
        nondirs = sortFiles(top,nondirs)
    # Recursively call walkTree on directories
    for dir in dirs:
        for x in walkTree(os.path.join(top,dir),onError,sortDir,sortFiles):
            yield x
    # Yield up files
    for file in nondirs:
        yield 'file', os.path.join(top,file)
    # Yield up the current directory
    yield 'dir', top

if __name__ == "__main__":
    dirName = raw_input("Directory to unzip? ")
    for t,n in walkTree(dirName):
        if t == 'file' and os.path.splitext(n)[-1] == '.zip':
            z = ZipFile(n,'r')
            for f in z.namelist():
                p,name = os.path.split(f)
                if name:
                    name = os.path.join(dirName,name)
                    print 'Unzipping ',name
                    fp = file(name,'wb')
                    fp.write(z.read(f))
                    fp.close()
                    
                
        
