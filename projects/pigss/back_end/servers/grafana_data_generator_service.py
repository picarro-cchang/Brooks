#!usr/bin/env/python3
""" Provides an API for generating and downloading user data files
"""

from os import listdir, path, stat, environ
from urllib.parse import parse_qs
import csv
from datetime import datetime

from aiohttp import web

from common.influx_connection import InfluxDBInstance
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.servers.service_template import ServiceTemplate
from back_end.grafana_data_generator_plugin.model import Model

log = LOLoggerClient(client_name="UserDataFileGenerator")


class GrafanaDataGeneratorService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_get("/api/getsavedfiles", self.get_files_meta)
        self.app.router.add_get("/api/getfile", self.send_file)
        self.app.router.add_get("/api/getkeys", self.get_user_keys)
        self.app.router.add_get("/api/generatefile", self.generate_file)
        self.app.router.add_route('GET', '/hello', self.hello)

    async def hello(self, request):
        return web.json_response(text="Hello")

    async def on_startup(self, app):
        log.info("GrafanaDataGeneratorService is starting up")

        self.app["config"] = self.app["farm"].config.get_gdg_plugin_config()

        # Create influxdb connection
        self.app["db_client"] = InfluxDBInstance(self.app["config"]["database"]).get_instance()

    async def on_shutdown(self, app):
        log.info("GrafanaDataGeneratorService is shutting down")

    async def on_cleanup(self, app):
        # Close influxdb connection
        if self.app["db_client"] is not None:
            InfluxDBInstance.close_connection()

    async def write_csv_file(self, result, data_dir, file_name):
        """ Writes result into csv file

        Arguments:
            result {list} -- list of points
            data_dir {str} -- destination directory where file needs to be saved
            file_name {str} -- name of the file

        Returns:
            boolean -- True if successfully saved, else False
        """
        file_path = f"{data_dir}/{file_name}"

        if path.exists(file_path) and path.isfile(file_name):
            return web.json_response({"message": "File already exists, try downloading it."})

        keys = result[0].keys()
        try:
            with open(file_path, "w+") as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(result)
            return True
        except IOError:
            return web.json_response(text="IO Error while writing the file.", status=503)
        except PermissionError:
            return web.json_response(text="Permission error occured while writing the file.", status=403)
        return False

    def chunks(self, stream, chunk_size=1024):
        """ Read a CSV file in chunks

        Arguments:
            stream {file} -- IO wrapper

        Keyword Arguments:
            chunk_size {int} -- (default: {1024})
        """
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def get_files_meta(self, request):
        """ Get files meta to be returned to frontend

        Returns:
            json response -- returns list of csv files present in data_dir
        """
        data_dir = self.app["config"]["server"]["data_dir"]

        try:
            # Filter only CSV files
            files = [f for f in listdir(data_dir) if f.endswith(self.app["config"]["server"]["file_type"])]
        except PermissionError:
            return web.json_response(text="OS Permission Error", status=404)

        files.sort(key=lambda name: name.lower())
        return web.json_response({"files": files})

    async def send_file(self, request):
        """ Send file to the user for download

        Arguments:
            request {Request}

        Returns:
            [Response] -- responsds with file if correct format and found
        """

        query_dict = parse_qs(request.query_string)
        data_dir = self.app["config"]["server"]["data_dir"]
        file_name = query_dict["name"][0]
        file_path = path.join(data_dir, file_name)
        file_type = self.app["config"]["server"]["file_type"]

        if not (file_name.endswith(file_type) and path.exists(file_path)):
            return web.HTTPNotFound()

        stats = stat(file_path)

        res = web.StreamResponse(headers={"Content-Disposition": f"Attachment; filename={file_name}"})
        res.content_type = file_type
        res.content_length = stats.st_size

        with open(file_path, "rb") as fl:
            await res.prepare(request)
            for chunk in self.chunks(fl):
                await res.write(chunk)
                await res.drain()
            await res.write_eof()
            res.force_close()
            return res

    async def generate_file(self, request):
        """Save the file on data_dir folder

        Returns:
            [filename: string] -- [filename if the file is successfully saved]
        """

        query_dict = parse_qs(request.query_string)
        query_params = {
            "keys": ",".join(query_dict["keys"]),
            "from": int(query_dict["from"][0]),
            "to": int(query_dict["to"][0]),
        }
        measurements = self.app["config"]["database"]["measurements"]
        result = await Model.get_points(self.app["db_client"], log, query_params, measurements)

        if len(result) == 0:
            data = {"message": "No observation in measurements"}
            return web.json_response(data=data, status=200)

        try:
            host_name = environ["HOSTNAME"]
            data_dir = self.app["config"]["server"]["data_dir"]

            # python's epoch time is in seconds
            time_from = datetime.fromtimestamp(query_params["from"] / 1000000000)
            time_to = datetime.fromtimestamp(query_params["to"] / 1000000000)

            from_formatted = time_from.strftime("%m-%d-%Y_%H%M%S")
            to_formatted = time_to.strftime("%m-%d-%Y_%H%M%S")

            file_name = f"{host_name}-{from_formatted}->{to_formatted}.csv"

            success = await self.write_csv_file(result, data_dir, file_name)
            if success:
                return web.json_response({"filename": file_name})
        except KeyError as ke:
            log.error("HOSTNAME enveironment variable is not defined.", ke)

    async def get_user_keys(self, request):
        """ Return the keys to the user which are not in admin_keys config

        Returns:
            json -- list of permissible user_keys
        """
        field_keys = await Model.get_field_keys(self.app["db_client"], log)
        user_keys = self.app["config"]["server"]["user_keys"]
        return web.json_response({"keys": list(filter(lambda x: x in field_keys, user_keys))})
