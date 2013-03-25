import os
import sys
import glob
from numpy import sqrt

def getSize(imageFile):
    return os.popen("identify %s" % imageFile, "r").read().split()[2]
    
def resize(tifFile, targetSizeP, targetDir=None):
    (dirname, basename) = os.path.split(tifFile)
    file, ext = os.path.splitext(basename)
    if not targetDir:
        targetDir = os.path.join(dirname, "PNG")
    if not os.path.isdir(targetDir):
        os.makedirs(targetDir)
    pngFile = os.path.join(targetDir, file + ".png")
    
    oldSize = getSize(tifFile)
    [h,w] = [float(i) for i in oldSize.split("x")]
    r = h/w
    newH = sqrt(targetSizeP*r)
    newW = newH/r
    os.popen("convert %s -sample %dx%d %s" % (tifFile, newH, newW, pngFile))
    newSize = getSize(pngFile)
    
    print "%s (%s) converted to %s (%s)" % (tifFile, oldSize, pngFile, newSize)
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        sourceFiles = sys.argv[1]
    else:
        sourceFiles = "*.tif"
    if len(sys.argv) > 2:
        targetSizeP = float(sys.argv[2])
    else:
        targetSizeP = 5000000
    if len(sys.argv) > 3:
        targetDir = sys.argv[3]
    else:
        targetDir = None
        
    for infile in glob.glob(sourceFiles):
        resize(infile, targetSizeP, targetDir)