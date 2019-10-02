from ruamel.yaml import YAML


class PigssConfig:
    def __init__(self, config_filename):
        self.yaml = YAML()
        self.config_filename = config_filename
        try:
            with open(config_filename, "r") as fp:
                self.config = self.yaml.load(fp.read())
        except Exception as e:
            raise ValueError(f"Error while processing YAML file {config_filename}.\n{e}")

    def get_simulation_analyzers(self):
        return self.config["Configuration"]["Simulation"]["analyzers"] if self.get_simulation_enabled() else []

    def get_simulation_enabled(self):
        return ("Simulation" in self.config["Configuration"] and self.config["Configuration"]["Simulation"].get("enabled", False))

    def get_simulation_random_ids(self):
        return self.get_simulation_enabled() and self.config["Configuration"]["Simulation"].get("random_ids", False)

    def get_http_server_port(self):
        return self.config["Configuration"]["HttpServer"]["port"]

    def get_http_server_listen_address(self):
        return self.config["Configuration"]["HttpServer"]["listen_address"]

    def get_services(self):
        return self.config["Services"]

    def get_time_series_database(self):
        return self.config["Configuration"]["Database"]
