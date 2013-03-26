import asyncore
import logging

class TcpServer(asyncore.dispatcher):
    """Receives connections and establishes handlers for each client.
    """
    
    def __init__(self, address):
        self.logger = logging.getLogger('TcpServer')
        asyncore.dispatcher.__init__(self)
        self.handler = None
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.logger.debug('binding to %s', self.address)
        self.listen(1)
        return

    def handle_accept(self):
        # Called when a client connects to our socket
        client_info = self.accept()
        self.logger.debug('handle_accept() -> %s', client_info[1])
        if self.handler is None or self.handler.closed:
            self.handler = TcpHandler(sock=client_info[0])
        else:
            GoAwayHandler(sock=client_info[0])
        # We only want to deal with one client at a time,
        # so close as soon as we set up the handler.
        # Normally you would not do this and the server
        # would run forever or until it received instructions
        # to stop.
        # self.handle_close()
    
    def handle_close(self):
        self.logger.debug('handle_close()')
        self.close()
        return
                
class GoAwayHandler(asyncore.dispatcher):
    """Tell client to go away and close the connection"""
    def __init__(self,sock,chunk_size=256):
        self.chunk_size = chunk_size
        self.logger = logging.getLogger('TcpHandler%s' % str(sock.getpeername()))
        asyncore.dispatcher.__init__(self, sock=sock)
        self.data_to_write = ["Go away, I am busy with another TCP connection."]
        
    def writable(self):
        """We want to write if we have received data."""
        response = bool(self.data_to_write)
        self.logger.debug('writable() -> %s', response)
        return response
    
    def handle_write(self):
        """Write as much as possible of the most recent message we have received."""
        data = self.data_to_write.pop()
        sent = self.send(data[:self.chunk_size])
        if sent < len(data):
            remaining = data[sent:]
            self.data.to_write.append(remaining)
        self.logger.debug('handle_write() -> (%d) "%s"', sent, data[:sent])
        if not self.writable():
            self.handle_close()
    
class TcpHandler(asyncore.dispatcher):
    """Handles echoing messages from a single client.
    """
    
    def __init__(self, sock, chunk_size=256):
        print "Creating new TcpHandler with sock %s" % sock
        self.chunk_size = chunk_size
        self.logger = logging.getLogger('TcpHandler%s' % str(sock.getpeername()))
        asyncore.dispatcher.__init__(self, sock=sock)
        self.data_to_write = ["Connected to Picarro TCP Server\r\n"]
        self.closed = False
        return
    
    def writable(self):
        """We want to write if we have received data."""
        response = bool(self.data_to_write)
        self.logger.debug('writable() -> %s', response)
        return response
    
    def handle_write(self):
        """Write as much as possible of the most recent message we have received."""
        data = self.data_to_write.pop()
        sent = self.send(data[:self.chunk_size])
        if sent < len(data):
            remaining = data[sent:]
            self.data.to_write.append(remaining)
        self.logger.debug('handle_write() -> (%d) "%s"', sent, data[:sent])

    def handle_read(self):
        """Read an incoming message from the client and put it into our outgoing queue."""
        data = self.recv(self.chunk_size)
        self.logger.debug('handle_read() -> (%d) "%s"', len(data), data)
    
    def handle_close(self):
        self.logger.debug('handle_close()')
        self.closed = True
        self.close()        

if __name__ == '__main__':
    import socket

    logging.basicConfig(level=logging.DEBUG,
                        format='%(name)s: %(message)s',
                        )

    address = ('localhost', 50000) # let the kernel give us a port
    server = TcpServer(address)
    
    asyncore.loop()