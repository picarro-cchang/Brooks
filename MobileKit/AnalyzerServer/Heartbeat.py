
from flask import Flask


class Heartbeat(object):

    @staticmethod
    def createFlaskApp():
        app = Flask(__name__)

        @app.route('/alive')
        def alive():
            return 'OK', 200

        return app
