import mmap
import time

# Check resources required to memory map a large file many times

start = time.clock()
size = 2**30    # 1 GiByte
with open("bigTempFile.txt","w+b") as f:
    map = mmap.mmap(f.fileno(),size)
    print "Flush returns:", map.flush()
    map.close()
print "Time to create %d byte file: %s" % (size,time.clock()-start)

# Map the file and time readback

readSize = 2**28    # 16 MiByte
for i in range(10):
    start = time.clock()
    with open("bigTempFile.txt","rb") as f:
        map = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
        map.read(readSize)
        map.close()
    print "Time to read %d bytes on pass %d is %s" % (readSize,i,time.clock()-start)

