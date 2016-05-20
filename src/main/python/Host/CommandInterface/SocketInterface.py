"""
File Name: SocketInterface.py
Purpose: Handles socket interface communication.

File History:
    06-10-29 ytsai  Created file
    09-07-03 alex   Cleaned up file

Copyright (c) 2010 Picarro, Inc. All rights reserved
"""

import sys
import time
import socket
import threading
import select

from SocketServer import BaseRequestHandler, TCPServer

class SocketInterface(object):
    def __init__(self):
        """ Initializes TCP Socket Interface """
        self.terminate = False
        self.sock      = None
        self.client    = None

    def config( self, port=None, backlog=1 ):
        self.port    = port
        self.backlog = backlog

    """
    # To use the regular accept() as below we need to add "self.sock.settimeout(0.5)" in self.open()
    def listener(self):
        while self.terminate==False:
            try:
                client, clientAddr = self.sock.accept()
                print "New client connected:", clientAddr
                if self.client != None:
                    self.client.close()
                self.client = client
            except:
                pass
    """

    def listener(self):
        (ir, iw, ie) = ([self.sock], [], [])
        while self.terminate==False:
            try:
                r, w, e = select.select(ir, iw, ie, 0.5)
                if r:
                    client, clientAddr = self.sock.accept()
                    print "New client connected:", clientAddr
                    if self.client != None:
                        self.client.close()
                    self.client = client
                else:
                    pass
            except:
                pass

    def open( self ):
        """ Opens port """
        if self.sock == None:
            self.close()
            self.terminate = False
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.sock.settimeout(0.5)
            self.sock.bind(('',self.port))
            self.sock.listen( self.backlog )
            self.sockThread = threading.Thread( target = self.listener )
            self.sockThread.setDaemon(True)
            self.sockThread.start()

    def close( self ):
        """ Closes port """
        if self.sock != None:
            self.sock.close()
            self.sock = None
        if  self.client != None:
            self.client.close()
            self.client = None
        self.terminate = True

    def read( self ):
        return self.client.recv(1)

    def write(self, msg):
        self.client.sendall(msg)

if __name__ == "__main__" :
    s = SocketInterface()
    s.config( port=88888, backlog=2 )
    s.open()
    while True:
        i = s.read()
        if i!= None and len(i):
            print "(%r)" % i
    s.close()