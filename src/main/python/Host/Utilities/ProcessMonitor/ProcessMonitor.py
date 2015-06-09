# Utility to find out CRDS processes running on a system and to gather memory use statistics

import cPickle
import psutil
import time
import math

if __name__ == "__main__":
    interval = 10.0
    now = time.time()
    next = math.ceil(now/interval) * interval
    fname = "ProcessMonitor_%d.pic" %  int(next)
    while True:
        time.sleep(next - time.time())
        now = time.time()
        procByPort = {}
        for proc in psutil.process_iter():
            for c in proc.get_connections():
                port = c.local_address[1]
                if 50000 <= port <= 51000:
                    # This is a Picarro RPC port
                    if port not in procByPort:
                        procByPort[port] = dict(pid=proc.pid, rss=proc.get_memory_info().rss)
        fp = open(fname,"ab")
        cPickle.dump((now,procByPort),fp,-1)
        fp.close()
        next = next + interval