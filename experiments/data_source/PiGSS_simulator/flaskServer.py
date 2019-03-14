from flask import Flask, jsonify, request
from flask_restplus import reqparse, abort, Api, Resource
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

@app.route("/testing", methods=['POST'])
def helloWorld():
    if not request.json:
        abort(400)
    print(request.json['message'])
    return jsonify(request.json), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888 ,debug=True)