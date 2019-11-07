from socketIO_client import SocketIO
import sys


def on_response(args):
    print(args)


if __name__ == '__main__':
    socketIO = SocketIO('localhost', 5001)
    while True:
        try:
            socketIO.on('update', on_response)
            socketIO.emit('update')
            socketIO.wait(seconds=1)
        except KeyboardInterrupt:
            sys.exit(0)

