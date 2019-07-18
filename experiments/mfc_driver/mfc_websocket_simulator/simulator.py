from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random


app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('update')
def test_connect():
    # print("Welcome, aaa received")
    emit('update', {'set_point': 5.0,
         'flow_rate': round(random.uniform(4.901, 5.101), 2)})


if __name__ == '__main__':
    socketio.run(app, port=5001)

