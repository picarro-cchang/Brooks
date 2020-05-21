#!/usr/bin/env python3
"""
Processes a yaml file which configures the sampling rack. All access
 to the configuration information should be made through methods in the PigssConfig
 class, so that configuration file format changes only require changes to this file.
"""
import os

from ruamel.yaml import YAML, YAMLError


# Decorator which provides a default value for a configuration parameter
def default(value):
    def wrapper(func):
        def wrapped_function(*a, **k):
            try:
                result = func(*a, **k)
            except KeyError:
                return value
            return result

        return wrapped_function

    return wrapper


class PigssConfig:
    def __init__(self, config_filename):
        self.yaml = YAML()
        self.config_filename = config_filename
        # The config_path attribute contains a prioritized list of directories used for
        #  as the base directory for configuration files specified in the YAML file as
        #  relative paths.
        if not os.path.exists(config_filename):
            raise FileNotFoundError(f"YAML configuration file {config_filename} does not exist")
        with open(config_filename, "r") as fp:
            try:
                self.config = self.yaml.load(fp.read())
            except YAMLError as e:
                raise ValueError(f"Error while processing YAML file {config_filename}.\n{e}")

    @default([])
    def get_simulation_analyzers(self):
        return self.config["Configuration"]["Simulation"]["analyzers"] if self.get_simulation_enabled() else []

    @default(False)
    def get_simulation_enabled(self):
        return ("Simulation" in self.config["Configuration"] and self.config["Configuration"]["Simulation"].get("enabled", False))

    @default(True)
    def get_simulation_ui_enabled(self):
        return self.get_simulation_enabled() and self.config["Configuration"]["Simulation"].get("ui_enabled", True)

    @default(False)
    def get_simulation_random_ids(self):
        return self.get_simulation_enabled() and self.config["Configuration"]["Simulation"].get("random_ids", False)

    @default(8000)
    def get_http_server_port(self):
        return int(self.config["Configuration"]["HttpServer"]["port"])

    @default("0.0.0.0")
    def get_http_server_listen_address(self):
        return self.config["Configuration"]["HttpServer"]["listen_address"]

    @default([])
    def get_services(self):
        return self.config["Services"]

    @default({"server": "localhost", "port": 8086, "name": "pigss_data"})
    def get_time_series_database(self):
        return self.config["Configuration"]["Database"]

    @default(50.0)
    def get_maximum_mfc_flow(self):
        return float(self.config["Settings"]["maximum_mfc_flow"])

    @default(40.0)
    def get_reference_mfc_flow(self):
        return float(self.config["Settings"]["reference_mfc_flow"])

    @default(1.0)
    def get_flow_settle_delay(self):
        return float(self.config["Settings"]["flow_settle_delay"])

    @default(30.0)
    def get_madmapper_startup_delay(self):
        return float(self.config["Settings"]["madmapper_startup_delay"])

    def get_rpc_tunnel_config_filename(self):
        try:
            config_filename = self.config["Configuration"]["RpcTunnel"]["config_file"]
        except KeyError:
            config_filename = "rpc_tunnel_configs.json"
        config_path = [
            os.getenv("PIGSS_CONFIG"),
            os.path.join(os.getenv("HOME"), ".config", "pigss"),
            os.path.dirname(os.path.abspath(self.config_filename))
        ]
        config_path = [p for p in config_path if p is not None and os.path.exists(p) and os.path.isdir(p)]

        for p in config_path:
            filename = os.path.normpath(os.path.join(p, config_filename))
            if os.path.exists(filename):
                return filename
        raise FileNotFoundError(f"Cannot find rpc_tunnel_config file {config_filename}")

    @default(None)
    def get_startup_plan(self):
        """If this key is absent, we do not automatically identify channels or loop
        a plan on startup. If the key is present, channel identification takes place,
        and if the file name is non-empty, it is used to specify the plan file
        (without the .pln extension)"""
        return self.config["Settings"]["startup_plan"]

    @default(None)
    def get_min_plan_interval(self):
        return self.config["Settings"]["min_plan_interval"]

    @default(None)
    def get_wait_warmup(self):
        return self.config["Settings"]["wait_warmup"]

    @default(1)
    def get_wait_warmup_timer(self):
        return self.config["Settings"]["wait_warmup_timer"]

    @default([])
    def get_glogger_plugin_config(self):
        return self.config["Plugins"]["GrafanaLogger"]

    @default([])
    def get_gdg_plugin_config(self):
        return self.config["Plugins"]["GrafanaDataGenerator"]

    @default([])
    def get_species(self):
        return self.config["Species"]
