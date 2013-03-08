import mmap
import time

# Read a file within a mmap

with open("sharedFile1.txt","rb") as f:
    map = mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
    while True:
        print map.readline()
        time.sleep(0.1)
        