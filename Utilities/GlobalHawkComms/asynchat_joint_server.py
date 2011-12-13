import asynchat
import asyncore
import logging

class TcpServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.handler = None
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(1)
        return
    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        if self.handler is None or self.handler.closed:
            self.handler = TcpHandler(sock=client_info[0])
        else:
            GoAwayHandler(sock=client_info[0])
    def handle_close(self):
        self.close()
        return
        
class UdpServer(asynchat.async_chat):
    def __init__(self,address):
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(address)
        self.set_terminator('\n')
        self.buffer = []
    def collect_incoming_data(self,data):
        self.buffer.append(data)
        # self.logger.debug('incoming_data -> %s', data)
    def found_terminator(self):
        print "UDP: %s" % "".join(self.buffer)
        self.buffer = []
        # self.logger.debug('found terminator')
    def handle_connect(self):
        pass
                
class GoAwayHandler(asynchat.async_chat):
    """Tell client to go away and close the connection"""
    def __init__(self,sock):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Server busy with existing TCP connection\r\n")
        self.close_when_done()
    def collect_incoming_data(self,data):
        return
    def found_terminator(self):
        return
    
class TcpHandler(asynchat.async_chat):
    """Handles processing data from a single client.
    """
    def __init__(self,sock):
        asynchat.async_chat.__init__(self,sock)
        self.set_terminator('\n')
        self.push("Connected to Picarro TCP server\r\n")
        self.closed = False
        self.buffer = []
    def collect_incoming_data(self,data):
        self.buffer.append(data)
    def found_terminator(self):
        print "TCP: %s" % "".join(self.buffer)
        self.buffer = []
    def handle_close(self):
        self.closed = True
        self.close()        

if __name__ == '__main__':
    import socket

    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s: %(message)s',
                        )

    TcpServer(('localhost', 50000))
    UdpServer(('localhost', 50001))
    
    asyncore.loop()