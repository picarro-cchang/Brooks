# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import logging
import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, make_response, send_file
from flask_cors import CORS, cross_origin


class RackNetworkSettingsServer(object):
    def __init__(self):
        pass

    def run(self):
        app = Flask(__name__)
        CORS(app)

        # endpoints
        @app.route('/get_instruments', methods = ['GET'])
        def end_point_get_instruments(): return self.get_instruments()

        @app.route('/apply_changes', methods = ['POST'])
        def end_point_apply_changes(): return self.apply_changes(request)

        @app.route('/destroy_instrument', methods = ['POST'])
        def end_point_destroy_instrument(): return self.destroy_instrument(request)

        @app.route('/restart_instrument', methods = ['POST'])
        def end_point_restart_instrument(): return self.restart_instrument(request)

        @app.route('/resolve_warning', methods = ['POST'])
        def end_point_resolve_warning(): return self.resolve_warning(request)

        @app.route('/get_network_settings', methods = ['GET'])
        def end_point_get_network_settings(): return self.get_network_settings()

        @app.route('/set_network_settings', methods = ['POST'])
        def end_point_set_network_settings(): return self.set_network_settings(request)


        # start flask server
        app.run(host='0.0.0.0', port=3030, debug=True)#, use_reloader=False)


    def get_instruments(self):
        return json.dumps(self.instruments)

    def apply_changes(self, request):
        data = request.get_json()
        with open("instruments_backend_meta.json","w") as f:
            f.write(json.dumps(data, indent=4, sort_keys=True))
        self.instruments = data
        return ""

    def destroy_instrument(self, request):
        ip = request.get_json()["ip"]
        with open("./img/explosion.txt","r") as f:
            exp = f.read()
        print(exp.format(ip))
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                instrument["warnings"] = []
                instrument["warnings"].append("instrument received a destroy warning at {}".format(datetime.datetime.now()))
        return ""

    def restart_instrument(self, request):
        ip = request.get_json()["ip"]
        print("instrument by {} will be restarted now".format(ip))
        return ""

    def resolve_warning(self, request):
        ip, resolved_warning = request.get_json()["warning"].split("@")
        print("instruments by {} warning '{}' is resolved".format(ip, resolved_warning))
        for instrument in self.instruments:
            if instrument["ip"] == ip:
                for warning in instrument["warnings"]:
                    if warning == resolved_warning:
                        instrument["warnings"].remove(warning)
        return ""

    def get_network_settings(self):
        with open("network_settings.json", "r") as f:
            settings = f.read()
            json_settings = json.dumps(settings)
        """
        settings = {
        'networkType': 'Static',
        'ip': '192.168.1.148',
        'gateway': '192.168.1.1',
        'netmask': '255.255.255.0',
        'dns': '8.8.8.8'
        }"""
        print(settings)
        return settings

    def set_network_settings(self, request):
        settings = request.get_json()
        with open("network_settings.json", "w") as f:
            f.write(json.dumps(settings, indent=4, sort_keys=True))
            f.write('\n')
        print(settings)
        return ""



if __name__ == '__main__':
    print(datetime.datetime.now())
    server = RackNetworkSettingsServer()
    server.run()
