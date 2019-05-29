#!/usr/bin/env python3

import os
import sys
import time
import json
import signal
import logging
import datetime
import threading
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, make_response, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit

port = 1337
filter_websocket_logs_out=True

class InstrumentsConfigurationServer(object):
    def __init__(self):
        # self.updates_since_last_check = {}
        self.dataFilename = "instruments_backend_meta_v2.json"
        self.filter_applyed_to_logger = False
        with open(self.dataFilename,"r") as f:
            self.instruments = json.loads(f.read())

        # logging.basicConfig(filename='example.log',level=10)

    def run(self):
        app = Flask(__name__)
        socketio = SocketIO(app)#, logger=True, engineio_logger =True)
        app.debug = True
        CORS(app)
        self.app = app

        # endpoints
        # @app.route('/is_has_updates', methods = ['GET', 'POST'])
        # def end_point_has_updates(): return self.has_updates(request)

        @app.route('/is_get_instruments', methods = ['GET', 'POST'])
        def end_point_get_instruments(): return self.get_instruments(request)

        @app.route('/is_apply_changes', methods = ['POST'])
        def end_point_apply_changes(): return self.apply_changes(request)
        
        @app.route('/is_changeDisplayName', methods = ['POST'])
        def end_point_changeDisplayName(): return self.changeDisplayName(request)
        

        @app.route('/is_set_instrument_positions', methods = ['POST'])
        def end_point_set_instrument_positions(): return self.set_instrument_positions(request)


        @app.route('/is_destroy_instrument', methods = ['POST'])
        def end_point_destroy_instrument(): return self.destroy_instrument(request)

        @app.route('/is_restart_instrument', methods = ['POST'])
        def end_point_restart_instrument(): return self.restart_instrument(request)

        @app.route('/is_resolve_warning', methods = ['POST'])
        def end_point_resolve_warning(): return self.resolve_warning(request)








        # @socketio.on('connect', namespace='/wb')
        # def test_connect():
        #     # self.ApplySocketFilterToLogger()
        #     # print("got connection")
        #     # emit('my response', {'data': 'Connected'})

        # @socketio.on('disconnect', namespace='/wb')
        # def test_disconnect():
        #     # self.ApplySocketFilterToLogger()
        #     # print('Client disconnected')


        # @socketio.on('message', namespace='/wb')
        # def test_message(message):
        #     # self.ApplySocketFilterToLogger()
            # print("FIRST CONTACE HERE: {}".format(message))
            # emit('event', {'data': 'YO, CONNECTED HEREaasdasdsasdd'})


        # add filter to the logs a second after the server starts
        if filter_websocket_logs_out:
            ApplySocketFilterToLoggerThread(self).start()

        # start flask server
        # app.run(host='0.0.0.0', port=3030, debug=True, use_reloader=True)
        socketio.run(app, 
            host='0.0.0.0', 
            port=port, 
            debug=True)

    def notify_websockets_about_update(self):
        emit("update", {"data":""}, namespace='/wb', broadcast=True)

    def get_instruments(self,request):
        try:
            data = request.get_json()
            print(data)
        except: pass
        return json.dumps(self.instruments)

    def apply_changes(self, request):
        data = request.get_json()

        print(json.dumps(data, indent=4, sort_keys=True))
        self.instruments = data
        self.update_made()
        return json.dumps(True)

    def changeDisplayName(self, request):
        data = request.get_json()

        for instrument in self.instruments:
            if instrument["ip"] == data["ip"]:
                instrument["displayName"]=data["newDisplayName"]

        self.update_made()
        return json.dumps(True)

    def update_made(self):
        self.save_to_file()
        self.notify_websockets_about_update()

    def save_to_file(self):
        with open(self.dataFilename,"w") as f:
            f.write(json.dumps(self.instruments, indent=4, sort_keys=True))
        

    def destroy_instrument(self, request):
        ip = request.get_json()["ip"]
        try:
            with open("./img/explosion.txt","r") as f:
                exp = f.read()
            print(exp.format(ip))
        except:pass
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                instrument["warnings"].append([
                    "{:%Y-%m-%d %H-%M-%S}".format(datetime.datetime.now()), 
                    "Instrument received a destroy signal. Don't worry, it was ignored."])
        self.update_made()
        return ""

    def restart_instrument(self, request):
        ip = request.get_json()["ip"]
        instrument_to_restart = None
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                instrument_to_restart = instrument

        if instrument_to_restart is not None:
            self.restartThread = RestartInstrument(instrument_to_restart, self)
            self.restartThread.start()
        return ""

    def change_instrument_status_by_ip(self, ip, new_status):
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                instrument["status"]=new_status


    def resolve_warning(self, request):
        data = request.get_json()
        ip = data["ip"]
        resolved_warning_timestamp = data["warning"]
        # ip, resolved_warning_timestamp = request.get_json()["warning"].split("#@#")
        print("instruments by {} warning '{}' is resolved".format(ip, resolved_warning_timestamp))
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                for warning in instrument["warnings"]:
                    if warning[0] == resolved_warning_timestamp:
                        instrument["warnings"].remove(warning)
        self.update_made()
        return ""

    def ApplySocketFilterToLogger(self):
        if  not self.filter_applyed_to_logger:
            logger = logging.getLogger('werkzeug')
            logger.addFilter(SocketLogFilter())
            self.filter_applyed_to_logger = True



class SocketLogFilter(logging.Filter):
    # filtering out all the logs about long polls
    def filter(self, record):
        keywords = ["transport=polling"]
        return not any([ (keyword in record.getMessage()) for keyword in keywords])
        # return not  ("socket" in record.getMessage())#.startswith('/socket')


class ApplySocketFilterToLoggerThread(threading.Thread):
    def __init__(self, app):
        super(ApplySocketFilterToLoggerThread,self).__init__()
        self.app = app
        return

    def run(self):
        time.sleep(1)
        self.app.ApplySocketFilterToLogger()




# this thread is a terrible practice, probably a ticking race condition bomb. 
# it is here only for testing purpose
class RestartInstrument(threading.Thread):
    def __init__(self, instrument_to_restart, server):
        super(RestartInstrument,self).__init__()
        self.instrument_to_restart = instrument_to_restart
        self.server = server
        return

    def run(self):
        self.instrument_to_restart["status_color"]="red"
        self.instrument_to_restart["status"]="OFF"

        with self.server.app.app_context():
            self.server.update_made()
        time.sleep(5)

        self.instrument_to_restart["status_color"]="blue"
        self.instrument_to_restart["status"]="starting..."
        with self.server.app.app_context():
            self.server.update_made()

        time.sleep(5)
        self.instrument_to_restart["status_color"]="green"
        self.instrument_to_restart["status"]="ON"
        with self.server.app.app_context():
            self.server.update_made()

        print("RESTART DONE")



if __name__ == '__main__':
    print(datetime.datetime.now())
    ICS = InstrumentsConfigurationServer()
    ICS.run()