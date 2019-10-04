#!/usr/bin/env python3
#
# FILE:
#   pigss_config.py
#
# DESCRIPTION:
#   Processes a yaml file which configures the sampling rack. All access
#  to the configuration information should be made through methods in the PigssConfig
#  class, so that configuration file format changes only require changes to this file.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze Initial check in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
import os

from ruamel.yaml import YAML


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
        self.config_dir = os.path.dirname(os.path.normpath(config_filename))
        try:
            with open(config_filename, "r") as fp:
                self.config = self.yaml.load(fp.read())
        except Exception as e:
            raise ValueError(f"Error while processing YAML file {config_filename}.\n{e}")

    @default([])
    def get_simulation_analyzers(self):
        return self.config["Configuration"]["Simulation"]["analyzers"] if self.get_simulation_enabled() else []

    @default(False)
    def get_simulation_enabled(self):
        return ("Simulation" in self.config["Configuration"] and self.config["Configuration"]["Simulation"].get("enabled", False))

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
            filename = self.config["Configuration"]["RpcTunnel"]["config_file"]
        except KeyError:
            filename = "rpc_tunnel_configs.json"
        return os.path.normpath(os.path.join(self.config_dir, filename))


if __name__ == "__main__":
    pc = PigssConfig("pigss_sim_config.yaml")
    print(pc.get_time_series_database())
