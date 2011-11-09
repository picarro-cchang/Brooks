import socket
import sys
import traceback
import msvcrt

if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.settimeout(10.0)
        while True:
            d = raw_input()
            sock.sendto(d+"\r\n",("localhost",8001))
            try:
                response = sock.recvfrom(2048)[0]
            except socket.error, socket.timeout:
                print "Socket error - check communications"
                continue
            sys.stdout.write(response)
    finally:
        sock.close()