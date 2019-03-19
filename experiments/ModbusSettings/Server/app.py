# Rest API using Python for querying data from mongodb

import os
import sys
from flask import Flask
import argparse
from flask_cors import CORS
import json
from Routes.NetworkRoutes import NetworkRoutes
from Module.NetworkModule import NetworkModule
from Module.ModbusSettingModule import ModbusSettingModule
from Routes.ModbusSettingRoutes import ModbusSettingsRoutes


class App:
    def __init__(self):

        # Create Fitter data routs object
        self.network_model_obj = NetworkModule()

        self.modebus_settings_model_obj = ModbusSettingModule()

        # Create flask app
        self.app = Flask(__name__)

        # Lets enable cross-Origin Resource sharing for Flask application
        CORS(self.app)

    def start_server(self, **setup):
        """
        Method use to register routs to Flask app and start Flask server
        :param setup:
        :return:
        """
        self.register_api()
        self.app.run(**setup)

    def register_api(self):
        """
        Method use to register routs
        :return:
        """

        # Register all RDF data related routs
        network_view = NetworkRoutes.as_view('/network', self.network_model_obj)
        self.app.add_url_rule('/network', view_func=network_view, methods=['GET'])

        # Register all modbus related routs
        modbus_settings_view = ModbusSettingsRoutes.as_view('/modbus_settings', self.modebus_settings_model_obj)
        self.app.add_url_rule('/modbus_settings', view_func=modbus_settings_view, methods=['GET', 'POST'])


def _handle_command_switches():
    """
    Method use to handle passed argument to app
    :return:
    """
    # lets parse argument and return required arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--json",
                        help="specify a config file: default = ./conf.json",
                        default="./conf.json")
    args = parser.parse_args()
    config_file = args.json
    return config_file


def _load_config(config_file):
    """
    Method use to get setting from ini file
    :param config_file:
    :return:
    """

    # check if ini files exist
    if os.path.exists(config_file):
        # Lets read json file and create config object
        with open(config_file) as f:
            config = json.load(f)
    else:
        # if file is not present exit application
        print("Configuration file not found: %s" % config_file)
        sys.exit(1)

    host = '0.0.0.0'
    port = 4000
    debug = True
    try:
        if 'Setup' in config:
            if 'Host_IP' in config['Setup']:
                host = config['Setup']['Host_IP']
            if 'Port' in config['Port']:
                port = config['Setup']['Port']
            if 'Debug_Mode' in config['Port']:
                debug = config['Setup']['Debug_Mode']
    finally:
        return {'host': host,
                'port': port,
                'debug': debug}


def main():
    # Handle command parameters
    config_file = _handle_command_switches()

    # Load configuration from ini file
    setup = _load_config(config_file)

    # Create flask application and start Flask server
    app_obj = App()
    app_obj.start_server(**setup)


if __name__ == "__main__":
    main()
