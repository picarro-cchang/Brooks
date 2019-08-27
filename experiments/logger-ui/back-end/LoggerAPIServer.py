from flask import Flask, request, g
from flask_restplus import Resource, Api, reqparse
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from resources.log import Log


app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

CORS(app)
api = Api(app)

api.add_resource(Log, '/hello')
api.add_resource(Log, '/logger/api/v1.0/getlogs')
api.add_resource(Log, '/logger/api/v1.0/getcolumns')


# @socketio.on('getlogs', namespace='/logger/api/v1.0/getlogs')
# def getLogs():
#     print("Return logs to front-end")
#     pass


# @socketio.on('connect', namespace='/test')
# def test_connect():
#     emit('my response', {'data': 'Connected'})


# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected')


# @app.teardown_appcontext
# def close_connection(exception):
#     connection = getattr(g, '_database', None)
#     if connection is not None:
#         connection.close()


if __name__ == '__main__':
    app.run(debug=True)
#     socketio.run(app)
