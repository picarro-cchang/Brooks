# Remote listener for data manager via ZMQ
# To run it in command prompt type:
#   ListenToZmq_plume.py -a[IP address of analyzer without brackets]
# Purpose: This program listens to ZMQ data stream. It saves a pickled .dat file
# in filedir specified in this code. It will ONLY save a file when the valve sequence
# changes value from 0. It also saves the previous 100 data samples BEFORE the valves switched values
# as it contains important data that triggered the plume acquisition.


import cPickle
from optparse import OptionParser
import zmq
from collections import deque #deque is a two-ended queue thingie
import os
import time
import pdb

BROADCAST_PORT_DATA_MANAGER_ZMQ = 45060
#filedir = r"C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\Colorado Field Campaign\data" #directory to save file
#filedir = r"C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\Texas field campaign\data"
#filedir = r"C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\Boston campaign\data"
#filedir = r"C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\EPA\data"
#filedir =r'C:\Users\ttsai\Desktop\Uintah Basin Field Campaign\DC'
filedir =r'C:\Users\ttsai\Desktop\Australia\data'

def timeprint (temp):
    localtime = time.localtime(temp)
    s = "%i_%i_%i__%i_%i" % (localtime.tm_year, localtime.tm_mon,\
    localtime.tm_mday, localtime.tm_hour, localtime.tm_min)
    return s

class DataManagerListener(object):
    def __init__(self, ipAddr, port):
        self.context = zmq.Context()
        self.listenSock = self.context.socket(zmq.SUB)
        self.listenSock.connect("tcp://%s:%d" % (ipAddr, port))
        self.listenSock.setsockopt(zmq.SUBSCRIBE, "")
        self.dataDeque = deque()
        self.maxlen = 100 #about 50 seconds worth of samples 
        self.filename = ""   #filename
        self.fp = None        #file pointer
        
    def run(self):
        poller = zmq.Poller()
        poller.register(self.listenSock, zmq.POLLIN)
        print "Running..."
        try:
            while True:
                socks = dict(poller.poll())
                if socks.get(self.listenSock) == zmq.POLLIN:
                    obj = cPickle.loads(self.listenSock.recv())
                    #print obj
                    if not obj["source"].startswith("analyze"): #filters out no data since it streams lots of stuff that has no data
                        continue #go back to the while loop
                    self.dataDeque.append(obj) #add to the right side of the deque
                    if len(self.dataDeque) > self.maxlen:
                        self.dataDeque.popleft() #the the deque is too long, start popping things out from left
                    if self.fp == None: #If no file is open
                        if obj["data"]["ValveMask"] > 0: #If valve is ON 
                            #Open file and start writing
                            self.filename = os.path.join(filedir, "plume_%d_%s.dat") \
                            %(int(obj["time"]), timeprint(obj["time"])) 
                            self.fp = open(self.filename, "wb") 
                            while len(self.dataDeque) >0: 
                                """                                
                                while there is still stuff in the deque, start writing onto the file
                                all the things in the deque i.e. the pre-trigger data until the deque
                                is empty. NOTE: During this loop, nothing is being added onto the deque
                                """
                                temp = self.dataDeque.popleft()
                                cPickle.dump(temp, self.fp, -1)
                                print "Writing valve %d at %d" % (int(temp["data"]["ValveMask"]), \
                                int(temp["time"]))
                    else:
                        while len(self.dataDeque)>0:
                            """
                            The file is already open, so keep add a value from the deque
                            """
                            obj = self.dataDeque.popleft()
                            if obj["data"]["ValveMask"] == 0:
                                self.fp.close()
                                self.fp = None
                                import plume_analyzerv24
                                #pdb.set_trace()
                                ans = plume_analyzerv24.plume_analyzer(self.filename)
                            else:
                                cPickle.dump(obj, self.fp, -1) 
                                print "Writing current valve %d at %d" % (int(obj["data"]["ValveMask"]),\
                                int(obj["time"]))                        
        finally:  # Get here on keyboard interrupt or other termination
            self.listenSock.close()
            self.context.term()


def main():
    parser = OptionParser()
    parser.add_option("-a", dest="ipAddr", default="127.0.0.1",
        help="IP address of analyzer (def: 127.0.0.1)")
    parser.add_option("-p", dest="port", default=BROADCAST_PORT_DATA_MANAGER_ZMQ,
        help="Data manager rebroadcaster port (def: %d)" % BROADCAST_PORT_DATA_MANAGER_ZMQ)
    (options, args) = parser.parse_args()
    dml = DataManagerListener(options.ipAddr, options.port)
    dml.run()

if __name__ == "__main__":
    main()
