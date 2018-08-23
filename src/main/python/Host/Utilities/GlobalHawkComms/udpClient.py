import socket
import sys
import traceback
import msvcrt

if __name__ == "__main__":
    addr = sys.argv[1] if len(sys.argv)>1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv)>2 else 8001
    cmd = []
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.connect((addr,port))
        sock.settimeout(0.1)
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                cmd.append(ch)
                sys.stdout.write(ch)
                if ch == "\r":
                    sock.sendall("".join(cmd)+"\n")
                    sys.stdout.write("\n")
                    cmd = []
            try:
                response = sock.recvfrom(2048)[0]
                sys.stdout.write(response)
            except socket.timeout:
                continue
            except socket.error:
                print "\r\nSocket error - check communications"
                continue
    finally:
        sock.close()