import asyncio
import json
import os

import attr
from aiomultiprocess import Process

from async_hsm import Ahsm, Event, Framework, Signal, Spy, TimeEvent, state
from async_hsm.SimpleSpy import SimpleSpy
from experiments.common.async_helper import log_async_exception
from experiments.common.rpc_ports import rpc_ports
from experiments.IDriver.DBWriter.InfluxDBWriter import InfluxDBWriter
from experiments.IDriver.IDriver import PicarroAnalyzerDriver
from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.madmapper.madmapper import MadMapper
from experiments.mfc_driver.alicat.alicat_driver import AlicatDriver
from experiments.relay_driver.numato.numato_driver import NumatoDriver
# from experiments.piglet.piglet_driver import PigletDriver
from experiments.state_machine.back_end.dummy_piglet_driver import PigletDriver
from experiments.state_machine.back_end.pigss_payloads import \
    SystemConfiguration
from experiments.testing.cmd_fifo import CmdFIFO

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

    @log_async_exception(log_func=log.warning, stop_loop=True)
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


class PigssSupervisor(Ahsm):
    def __init__(self, farm=None):
        log.info("Starting PigssSupervisor")
        self.farm = farm
        self.farm.RPC = {}
        self.process_wrappers = {}  # List of Process objects
        self.tasks = []
        self.device_dict = {}
        self.bank_list = []
        with open(tunnel_configs, "r") as f:
            self.rpc_tunnel_config = json.loads(f.read())
        log.info(f"RPC Tunnel settings loaded from {tunnel_configs}")

    @state
    def _initial(self, e):
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("TERMINATE", self)
        return self.tran(self._operational)

    @state
    def _exit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            for wrapper in self.process_wrappers.values():
                wrapper.process.kill()
            return self.handled(e)
        return self.super(self.top)

    @state
    def _operational(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.tasks.append(asyncio.create_task(self.startup_processes()))
            return self.handled(e)
        elif sig == Signal.SYSTEM_CONFIGURE:
            self.tasks.append(asyncio.create_task(self.error_recovery(5.0)))
            return self.handled(e)
        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)
        return self.super(self.top)

    async def setup_processes(self, at_start=True):
        if at_start:
            self.bank_list = []
        if at_start or self.process_wrappers["MadMapper"].killed:
            process_wrapper = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'), "MadMapper")
            self.process_wrappers["MadMapper"] = process_wrapper
            self.farm.RPC["MadMapper"] = await process_wrapper.start()
            # self.device_dict = await self.farm.RPC["MadMapper"].read_json()
            self.device_dict = await self.farm.RPC["MadMapper"].map_devices(True)
            log.info(f"\nResult of MadMapper.map_devices {self.device_dict}")
            if at_start:
                self.tasks.append(asyncio.create_task(process_wrapper.pinger(5)))
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
                        self.bank_list.append(dev_params["Bank_ID"])
                        self.tasks.append(asyncio.create_task(process_wrapper.pinger(2)))
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
                        self.tasks.append(asyncio.create_task(process_wrapper.pinger(2)))
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
                        self.tasks.append(asyncio.create_task(process_wrapper.pinger(2)))
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
                                                                          "valve_pos": 0,
                                                                          "analyzer": analyzer,
                                                                          "chassis": chassis
                                                                      })
                    if at_start:
                        self.tasks.append(asyncio.create_task(process_wrapper.pinger(2)))
                    else:
                        log.info(f"Restarted IDriver: {key}")

    @log_async_exception(log_func=log.warning, stop_loop=True)
    async def startup_processes(self):
        await self.setup_processes(at_start=True)
        Framework.publish(
            Event(Signal.SYSTEM_CONFIGURE, SystemConfiguration(bank_list=sorted(self.bank_list),
                                                               mad_mapper_result=self.device_dict)))

    @log_async_exception(log_func=log.warning, stop_loop=True)
    async def error_recovery(self, period):
        while True:
            await asyncio.sleep(period)
            await self.setup_processes(at_start=False)
