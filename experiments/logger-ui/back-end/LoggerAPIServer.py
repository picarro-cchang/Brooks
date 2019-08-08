from flask import Flask, request, g
from flask_restplus import Resource, Api, reqparse

from resources.log import Log


app = Flask(__name__)
api = Api(app)

api.add_resource(Log, '/hello')
api.add_resource(Log, '/logger/api/v1.0/log')


@app.teardown_appcontext
def close_connection(exception):
    connection = getattr(g, '_database', None)
    if connection is not None:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)
