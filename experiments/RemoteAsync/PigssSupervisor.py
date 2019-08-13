import asyncio
import json
import os

import attr
from aiomultiprocess import Process

from experiments.testing.cmd_fifo import CmdFIFO
from experiments.common.rpc_ports import rpc_ports
from experiments.IDriver.DBWriter.InfluxDBWriter import InfluxDBWriter
from experiments.IDriver.IDriver import PicarroAnalyzerDriver
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.madmapper.madmapper import MadMapper
from experiments.mfc_driver.alicat.alicat_driver import AlicatDriver
from experiments.piglet.piglet_driver import PigletDriver
from experiments.relay_driver.numato.numato_driver import NumatoDriver

host = "10.100.3.28"
port = rpc_ports.get('madmapper')

my_path = os.path.dirname(os.path.abspath(__file__))
tunnel_configs = os.path.normpath(os.path.join(my_path, 'rpc_tunnel_configs.json'))

log = LOLoggerClient(client_name="PigssSupervisor", verbose=True)


class AsyncWrapper:
    """Returns asynchronous version of a method by wrapping it in an executor"""

    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, attr):
        return AsyncWrapper(getattr(self.proxy, attr))

    async def __call__(self, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(None, self.proxy, *args, **kwargs)


@attr.s
class ProcessWrapper:
    driver = attr.ib()
    rpc_port = attr.ib(type=int)
    name = attr.ib(type=str)
    process = attr.ib(None, type=Process)
    rpc_wrapper = attr.ib(None)
    killed = attr.ib(False)

    async def start(self, *args, **kwargs):
        async def start_driver():
            d = self.driver(*args, **kwargs)
            d.rpc_serve_forever()

        if self.process is not None and self.process.is_alive():
            self.process.kill()
            await self.process.join()
        log.info(f"Starting process {self.name}.")
        self.process = Process(target=start_driver)
        self.process.daemon = True
        self.process.start()
        self.rpc_wrapper = AsyncWrapper(CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{self.rpc_port}", "PigssSupervisor"))
        await asyncio.sleep(0.1)
        return self.rpc_wrapper

    async def pinger(self, period):
        try:
            while True:
                await asyncio.sleep(period)
                if await asyncio.wait_for(self.rpc_wrapper.CmdFIFO.PingFIFO(), timeout=2 * period) == 'Ping OK':
                    print("+", end="", flush=True)
        except CmdFIFO.RemoteException:
            log.warning(f"Ping to process {self.name} raised exception. Killing process.")
            self.process.kill()
            self.killed = True
        except asyncio.TimeoutError:
            log.warning(f"Ping to process {self.name} timed out. Killing process.")
            self.process.kill()
            self.killed = True


async def dotty():
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.5)


class PigssSupervisor:
    def __init__(self, farm=None):
        log.info("Starting PigssSupervisor")
        self.farm = farm
        self.process_wrappers = {}  # List of Process objects
        self.device_dict = {}
        with open(tunnel_configs, "r") as f:
            self.rpc_tunnel_config = json.loads(f.read())
        log.info(f"RPC Tunnel settings loaded from {tunnel_configs}")

    async def setup_processes(self, at_start=True):
        if at_start or self.process_wrappers["MadMapper"].killed:
            process_wrapper = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'), "MadMapper")
            self.process_wrappers["MadMapper"] = process_wrapper
            self.farm.RPC["MadMapper"] = await process_wrapper.start()
            # self.device_dict = await self.farm.RPC["MadMapper"].read_json()
            self.device_dict = await self.farm.RPC["MadMapper"].map_devices(True)
            log.info(f"\nResult of MadMapper.map_devices {self.device_dict}")
            if at_start:
                asyncio.create_task(process_wrapper.pinger(5))
            else:
                log.info(f"Restarted Madmapper")
        for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
            if dev_params['Driver'] == 'PigletDriver':
                if at_start or self.process_wrappers[key].killed:
                    name = f"Piglet_{dev_params['Bank_ID']}"
                    process_wrapper = ProcessWrapper(PigletDriver, dev_params['RPC_Port'], name)
                    self.process_wrappers[key] = process_wrapper
                    self.farm.RPC[name] = await process_wrapper.start(port=dev_params['Path'],
                                                                      rpc_port=dev_params['RPC_Port'],
                                                                      baudrate=dev_params['Baudrate'])
                    if at_start:
                        asyncio.create_task(process_wrapper.pinger(2))
                    else:
                        log.info(f"Restarted piglet driver: {key}")
            elif dev_params['Driver'] == 'AlicatDriver':
                if at_start or self.process_wrappers[key].killed:
                    name = "MFC"
                    process_wrapper = ProcessWrapper(AlicatDriver, dev_params['RPC_Port'], name)
                    self.process_wrappers[key] = process_wrapper
                    self.farm.RPC[name] = await process_wrapper.start(port=dev_params['Path'],
                                                                      rpc_port=dev_params['RPC_Port'],
                                                                      baudrate=dev_params['Baudrate'])
                    if at_start:
                        asyncio.create_task(process_wrapper.pinger(2))
                    else:
                        log.info(f"Restarted Alicat driver: {key}")
            elif dev_params['Driver'] == 'NumatoDriver':
                if at_start or self.process_wrappers[key].killed:
                    relay_id = dev_params['Numato_ID']
                    name = f"Relay_{relay_id}"
                    process_wrapper = ProcessWrapper(NumatoDriver, dev_params['RPC_Port'], name)
                    self.process_wrappers[key] = process_wrapper
                    self.farm.RPC[name] = await process_wrapper.start(device_port_name=dev_params['Path'],
                                                                      rpc_server_port=dev_params['RPC_Port'])
                    if at_start:
                        asyncio.create_task(process_wrapper.pinger(2))
                    else:
                        log.info(f"Restarted Numato driver: {key}")

        for key, dev_params in sorted(self.device_dict['Devices']['Network_Devices'].items()):
            if dev_params['Driver'] == 'IDriver':
                if at_start or self.process_wrappers[key].killed:
                    name = f"Picarro_{dev_params['SN']}"
                    process_wrapper = ProcessWrapper(PicarroAnalyzerDriver, dev_params['RPC_Port'], name)
                    self.process_wrappers[key] = process_wrapper
                    chassis, analyzer = dev_params['SN'].split("-")
                    self.farm.RPC[name] = await process_wrapper.start(instrument_ip_address=dev_params['IP'],
                                                                      database_writer=InfluxDBWriter(),
                                                                      rpc_server_port=dev_params['RPC_Port'],
                                                                      rpc_server_name=name,
                                                                      start_now=True,
                                                                      rpc_tunnel_config=self.rpc_tunnel_config,
                                                                      database_tags={
                                                                          "analyzer": analyzer,
                                                                          "chassis": chassis
                                                                      })
                    if at_start:
                        asyncio.create_task(process_wrapper.pinger(2))
                    else:
                        log.info(f"Restarted IDriver: {key}")

    async def error_recovery(self, period):
        while True:
            await asyncio.sleep(period)
            await self.setup_processes(at_start=False)

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        log.error(f"Unhandled exception: {msg}")
        loop.stop()

    async def main(self):
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(self.handle_exception)
        try:
            await self.setup_processes(at_start=True)
            await self.error_recovery(5.0)
        finally:
            log.info("Program terminated")
