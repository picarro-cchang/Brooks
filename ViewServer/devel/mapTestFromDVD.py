import mmap
import time

# Check resources required to memory map a large file many times


# Map the file and time readback

readSize = 2**28    # 256 MiByte
for i in range(10):
    start = time.clock()
    with open("C:\Users\Sze\Documents\VboxShared\Downloads\Connections 3\Connections3.10of10.myTVblog.org.avi\Connections3.10of10.myTVblog.org.avi","rb") as f:
        map = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
        map.read(readSize)
        map.close()
    print "Time to read %d bytes on pass %d is %s" % (readSize,i,time.clock()-start)

