#!/usr/bin/env python
import socket
import sys
import Queue
from threading import Thread

HOST = 'localhost'
PORT = 5193

class Receiver(object):
    def __init__(self):
        self.queue = Queue.Queue(0)
        self.sock = None
        self.getThread = None
        
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            raise
            
    def getFromSocket(self):
        try:
            while True:
                data = self.sock.recv(1024)
                if len(data)>0:
                    for c in data: 
                        self.queue.put(c)
        finally:
            self.sock.close()
            
    def run(self):
        self.connect()
        print "Connection OK"
        self.getThread = Thread(target=self.getFromSocket) 
        self.getThread.setDaemon(True)
        self.getThread.start()
        state = "SYNC1"
        value = 0
        counter = 0
        while True:
            try:
                c = self.queue.get(timeout=20.0)
            except Queue.Empty:
                break
            if state == "SYNC1":
                if ord(c) == 0x5A: state = "SYNC2"
            elif state == "SYNC2":
                if ord(c) == 0xA5: 
                    value, counter, maxcount = 0, 0, 8
                    state = "TIMESTAMP"
                else:
                    state = "SYNC1"
            elif state == "TIMESTAMP":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    ts = value
                    state = "PORT"
            elif state == "PORT":
                port = ord(c)
                value, counter, maxcount = 0, 0, 2
                state = "BYTECOUNT"
            elif state == "BYTECOUNT":
                value += ord(c)<<(8*counter)
                counter += 1
                if counter == maxcount:
                    print ts, port, value
                    counter, maxcount = 0, value
                    state = "DATA"
            elif state == "DATA":
                if c not in ['\r','\n']: 
                    sys.stdout.write(c)
                counter += 1
                if counter == maxcount:
                    sys.stdout.write('\n')
                    state = "SYNC1"

if __name__ == "__main__":
    r = Receiver()
    r.run()