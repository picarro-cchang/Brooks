import json
import time

from aiohttp import web
from aioinflux import iterpoints

from experiments.IDriver.DBWriter.AioInfluxDBWriter import AioInfluxDBWriter


class PortHistoryService:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/", self.health_check)
        # self.app.router.add_route("GET", "/search", self.search)
        self.app.router.add_route("POST", "/search", self.search)
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)
        self.bank_names = None
        self.end_time = "now"
        self.default_available_ports = {"1": 255, "2": 255, "3": 255, "4": 255}
        self.default_bank_names = {
            "1": {
                "name": "Bank 1",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "2": {
                "name": "Bank 2",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "3": {
                "name": "Bank 3",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "4": {
                "name": "Bank 4",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            }
        }
        self.available_ports = self.default_available_ports
        self.bank_names = self.default_bank_names

    async def on_startup(self, app):
        db_config = self.app['farm'].config.get_time_series_database()
        self.db_writer = AioInfluxDBWriter(address=db_config["server"], db_port=db_config["port"], db_name=db_config["name"])

    async def on_shutdown(self, app):
        print("BankName server is shutting down")

    async def health_check(self, request):
        """
        description: Used to check theat data source exists and works

        tags:
            -   port history service
        summary: Used to check theat data source exists and works
        produces:
            -   application/text
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text='This datasource is healthy.')

    async def search(self, request):
        """
        description: Gets the names of the valves available

        tags:
            -   port history service
        summary:  Gets the names of the valves available

        consumes:
            -   application/json
        parameters:
            -   in: body
                name: query
                description: Specify what to retrieve
                required: false
                schema:
                    type: object
                    properties:
                        target:
                            type: string
                            description: search string in JSON format, which can be a time range as an array of an object with type and range keys 
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        # The query can be a range with a list of start and end times in ms since epoch, or a dictionary
        #  with keys "range" and "type".

        # start_ms and end_ms are the Grafana time range for the plots
        result_type = "ports"
        query = (await request.json()).get('target', None)
        if query is not None:
            query = json.loads(query)
        if isinstance(query, list):
            start_ms, end_ms = query
        elif isinstance(query, dict):
            start_ms, end_ms = query.get("range", (0, int(1000 * time.time())))
            result_type = query.get("type", "ports")
        else:
            start_ms = 0
            end_ms = int(1000 * time.time())

        if end_ms != self.end_time:
            self.bank_names = self.default_bank_names
            self.available_ports = self.default_available_ports
            influx_query = f"select bank_names, available_ports from port_history where time<{end_ms}ms order by time desc limit 1"
            data = await self.db_writer.read_data(influx_query)
            result = list(iterpoints(data))
            if result:
                time_ms = result[0][0] // 1000000
                # If the end of the time window is close to (within 30s) of the current time, or if the most recent history
                #  record has a timestamp before start_ms, use the information in that record
                if abs(1000 * time.time() - end_ms) < 30000 or time_ms < start_ms:
                    self.bank_names = json.loads(result[0][1])
                    self.available_ports = json.loads(result[0][2])
        self.end_time = end_ms

        banks = []
        ports = []
        valve_pos = 1
        for bank in [1, 2, 3, 4]:
            available = self.available_ports[str(bank)]
            bank_dict = self.bank_names[str(bank)]
            if available != 0:
                banks.append(dict(text=f"{bank_dict['name']}", value=str(1 << (bank - 1))))
            for channel in [1, 2, 3, 4, 5, 6, 7, 8]:
                chan_dict = bank_dict["channels"]
                descr = f"{bank_dict['name']} {chan_dict[str(channel)]}"
                if available & (1 << (channel - 1)):
                    ports.append(dict(text=f"{valve_pos}: {descr}", value=str(valve_pos)))
                valve_pos += 1
        return web.json_response(ports if result_type == "ports" else banks)

    # async def query(self, request):
    #     """
    #     ---
    #     description: Make a query to the database

    #     tags:
    #         -   port history service
    #     summary: make a query to the database
    #     consumes:
    #         -   application/json
    #     produces:
    #         -   application/json
    #     parameters:
    #         -   in: body
    #             name: query
    #             description: Specify query
    #             required: true
    #             schema:
    #                 type: object
    #     responses:
    #         "200":
    #             description: successful operation
    #     """
    #     req = await request.json()
    #     start_time_ms = int(req['scopedVars']['__from']['value'])
    #     stop_time_ms = int(req['scopedVars']['__to']['value'])
    #     raw_range = req['rangeRaw']
    #     if raw_range["to"] == "now":
    #         controller = request.app['farm'].controller
    #         self.bank_names = controller.get_bank_names()
    #     elif raw_range["to"] != self.end_time:
    #         print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {raw_range["to"]}')
    #         stop_time = raw_range['to']
    #         data = await self.db_writer.read_data(f"select bank_name_data from bank_name_data where time <= '{stop_time}' order by time desc limit 1")
    #         result = list(iterpoints(data))
    #         print(f'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {result[0] if result else "Empty"}')
    #         # stop_time_ms
    #         # We need to update self.bank_names from the influx database
    #         pass
    #     self.end_time = raw_range["to"]

    #     banks = [1, 2, 3, 4]
    #     channels = [1, 2, 3, 4, 5, 6, 7, 8]

    #     def valve_pos(bank, channel):
    #         return 8 * (bank - 1) + channel

    #     columns = []
    #     rows = []
    #     names = {}
    #     for bank in banks:
    #         bank_dict = self.bank_names[str(bank)]
    #         columns.append({"text": bank_dict['name'], "type": "string"})
    #         chan_dict = bank_dict["channels"]
    #         names[bank] = {channel: f"{valve_pos(bank, channel): 2}: {chan_dict[str(channel)]}" for channel in channels}
    #     for channel in channels:
    #         rows.append([names[bank][channel] for bank in banks])
    #     return web.json_response([{"columns": columns, "rows": rows, "type": "table"}])
