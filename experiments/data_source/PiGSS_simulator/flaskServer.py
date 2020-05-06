import logging

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restplus import Api, Resource, abort, reqparse

import CmdFIFO

app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

Host = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % 51234,
                                  "Flask RPC Caller", IsDontCareConnection=False)


@app.route("/print", methods=['POST'])
def printer():
    if not request.json:
        abort(400)
    print(request.json['message'])
    Host.printer(request.json['message'])
    return jsonify(request.json), 200

@app.route("/valve_mode", methods=['GET', 'POST'])
def valve_mode():
    if request.method == 'POST':
        if not request.json:
            abort(400)
        print("Valve Mode:", request.json['mode'])
        Host.set_valve_mode(int(request.json['mode']))
        return jsonify({"mode": Host.get_valve_mode()}), 200
    else:
        return jsonify({"mode": Host.get_valve_mode()}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
