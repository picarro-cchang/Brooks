# Flask server for application logs from CRDS analyzer processes

from flask import abort, Flask, make_response, jsonify, request, send_file
from flask_socketio import SocketIO, emit, rooms
import os
import threading
import time
import eventlet.green.zmq as zmq

PORT = 40005

app = Flask(__name__, static_url_path='', static_folder='../../js/Applog/src/', template_folder='../../js/Applog/src/')
socketio = SocketIO(app, async_mode="eventlet")
app.add_url_rule('/', 'index', lambda: app.send_static_file('index.html'))
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)

def get_applog():
    context    = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:%d" % (PORT,))
    subscriber.setsockopt(zmq.SUBSCRIBE, "")
    print "Starting get_applog"
    while True:
        message = subscriber.recv_string()
        try:
            socketio.emit("applog", dict(message=message))
        except:
            print "Cannot send to web socket"
            socketio.sleep(0.5)

@socketio.on('connect')
def test_connect():
    emit('socket_id', dict(socket_id=request.sid))
    print('web socket connected: ', request.sid)
    socketio.start_background_task(get_applog)

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 3000)), debug=True)