import asyncio
import json
import os
import time
from collections import deque

import attr
from aiomultiprocess import Process

from async_hsm import Ahsm, Event, Framework, Signal, Spy, TimeEvent, state
from async_hsm.SimpleSpy import SimpleSpy
from experiments.common.async_helper import log_async_exception
from experiments.IDriver.IDriver import PicarroAnalyzerDriver
from experiments.state_machine.back_end.dummy_influx_writer import \
    InfluxDBWriter
from experiments.state_machine.back_end.dummy_logger import DummyLoggerClient
from experiments.state_machine.back_end.dummy_piglet_driver import PigletDriver
from experiments.state_machine.back_end.pigss_payloads import \
    SystemConfiguration
from experiments.testing.cmd_fifo import CmdFIFO

my_path = os.path.dirname(os.path.abspath(__file__))
log = DummyLoggerClient(client_name="DummySupervisor", verbose=True)
tunnel_configs = os.path.normpath(os.path.join(my_path, 'rpc_tunnel_configs.json'))


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
    start_time = attr.ib(0.0, type=float)
    stop_time = attr.ib(None)
    dev_name = attr.ib("")
    stop_reason = attr.ib("")

    async def start(self, *args, **kwargs):
        async def start_driver():
            d = self.driver(*args, **kwargs)
            d.rpc_serve_forever()

        if self.process is not None and self.process.is_alive():
            self.process.kill()
            await self.process.join()
        log.info(f"Starting process {self.name}.")
        self.start_time = time.time()
        self.process = Process(target=start_driver)
        self.process.daemon = True
        self.process.start()
        self.rpc_wrapper = AsyncWrapper(CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{self.rpc_port}", "PigssSupervisor"))
        await asyncio.sleep(0.1)
        return self.rpc_wrapper

    async def stop_process(self, stop_reason="Unknown"):
        if self.process.is_alive():
            self.process.kill()
        if self.stop_time is None:
            self.stop_time = time.time()
            self.stop_reason = stop_reason
        await self.process.join()

    @log_async_exception(stop_loop=True)
    async def pinger(self, period):
        try:
            while True:
                await asyncio.sleep(period)
                if await asyncio.wait_for(self.rpc_wrapper.CmdFIFO.PingFIFO(), timeout=2 * period) == 'Ping OK':
                    print("+", end="", flush=True)
        except CmdFIFO.RemoteException:
            log.warning(f"Ping to process {self.name} raised exception. Killing process.")
            await self.stop_process("Ping to process raised exception.")
        except asyncio.TimeoutError:
            log.warning(f"Ping to process {self.name} timed out. Killing process.")
            await self.stop_process("Ping to process timed out.")


class DummySupervisor(Ahsm):
    def __init__(self, farm=None):
        super().__init__()
        self.farm = farm
        print("Starting DummySupervisor")
        self.wrapped_processes = {}  # List of ProcessWrapper objects
        self.farm.RPC = {}  # Asynchronous interface to RPC handlers of spervisees
        self.device_dict = {}
        self.tasks = []
        self.old_processes = deque(maxlen=32)
        self.te = TimeEvent("MONITOR_PROCESSES")
        self.mon_task = None
        with open(tunnel_configs, "r") as f:
            self.rpc_tunnel_config = json.loads(f.read())
        log.info(f"RPC Tunnel settings loaded from {tunnel_configs}")

    def get_device_map(self):
        return self.device_dict

    def get_processes(self):
        processes = []

        def append_process_dict(wrapped_process):
            processes.append({
                "device": wrapped_process.dev_name,
                "rpc_name": wrapped_process.name,
                "rpc_port": wrapped_process.rpc_port,
                "driver": wrapped_process.driver.__name__,
                "pid": wrapped_process.process.pid,
                "daemon": wrapped_process.process.daemon,
                "is_alive": wrapped_process.process.is_alive(),
                "exitcode": wrapped_process.process.exitcode,
                "start_time": wrapped_process.start_time,
                "stop_time": wrapped_process.stop_time,
                "stop_reason": wrapped_process.stop_reason
            })

        for dev_name in self.wrapped_processes:
            append_process_dict(self.wrapped_processes[dev_name])
        for wrapped_process in self.old_processes:
            append_process_dict(wrapped_process)
        return processes

    @state
    def _initial(self, e):
        Framework.subscribe("MADMAPPER_DONE", self)
        Framework.subscribe("PROCESSES_STARTED", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("TERMINATE", self)
        Framework.subscribe("PROCESSES_MONITORED", self)
        return self.tran(self._operational)

    @state
    def _exit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            for wrapper in self.wrapped_processes.values():
                wrapper.process.kill()
            return self.handled(e)
        return self.super(self.top)

    @state
    def _operational(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._mapping)
        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)
        return self.super(self.top)

    @state
    def _mapping(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.tasks.append(asyncio.create_task(self.dummy_mapper()))
            return self.handled(e)
        elif sig == Signal.MADMAPPER_DONE:
            payload = e.value
            self.device_dict = payload.copy()
            self.bank_list = []
            for name, descr in payload["Devices"]["Serial_Devices"].items():
                if descr["Driver"] == "PigletDriver":
                    self.bank_list.append(descr["Bank_ID"])
            self.tasks.append(asyncio.create_task(self.start_processes()))
            return self.handled(e)
        elif sig == Signal.PROCESSES_STARTED:
            Framework.publish(
                Event(Signal.SYSTEM_CONFIGURE,
                      SystemConfiguration(bank_list=sorted(self.bank_list), mad_mapper_result=self.device_dict)))
            return self.tran(self._supervising)
        return self.super(self._operational)

    @state
    def _supervising(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            ## TODO: Change to a symbolic constant
            self.te.postIn(self, 4.0)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.te.disarm()
            return self.handled(e)
        elif sig == Signal.SYSTEM_CONFIGURE:
            print(f"System config: {e.value}")
            return self.handled(e)
        elif sig == Signal.MONITOR_PROCESSES:
            print(f"STARTING MONITOR PROCESSES {time.time()}")
            self.mon_task = asyncio.create_task(self.monitor_processes())
            self.tasks.append(self.mon_task)
            return self.handled(e)
        elif sig == Signal.PROCESSES_MONITORED:
            self.tasks.remove(self.mon_task)
            self.te.postIn(self, 4.0)
            return self.handled(e)
        return self.super(self._operational)

    async def start_processes(self):
        await self.setup_processes(at_start=True)
        Framework.publish(Event(Signal.PROCESSES_STARTED, None))

    async def monitor_processes(self):
        await self.setup_processes(at_start=False)
        Framework.publish(Event(Signal.PROCESSES_MONITORED, None))

    @log_async_exception(stop_loop=True)
    async def dummy_mapper(self):
        with open(os.path.join(my_path, "madmapper.json"), "r") as fp:
            mapper_dict = json.load(fp)
            await asyncio.sleep(3.0)
            Framework.publish(Event(Signal.MADMAPPER_DONE, mapper_dict))

    async def register_process(self, key, wrapped_process, rpc_name, ping_period, at_start, **process_kwargs):
        """Store the `wrapped_process` in the wrapped_processes dictionary under the keyname `key`, archiving 
            any process already there into `old_processes`. This `wrapped_process` contains a Driver with an
            RPC server which is registered with the farm under the name `rpc_name`. If this is the first time 
            that this is run for a process, `at_start` is True, and we also start a ping process to check the 
            health of the RPC server every `ping_period` seconds. When the Driver is constructed, it is passed
            ``process_kwargs`` as its arguments.
        """
        if key in self.wrapped_processes:
            await self.wrapped_processes[key].stop_process("Found dead by process monitor")
            self.old_processes.append(self.wrapped_processes[key])
        self.wrapped_processes[key] = wrapped_process
        self.farm.RPC[rpc_name] = await wrapped_process.start(**process_kwargs)
        if at_start:
            self.tasks.append(asyncio.create_task(wrapped_process.pinger(ping_period)))
        else:
            log.info(f"Restarted {wrapped_process.driver.__name__} at {key}")
        return

    @log_async_exception(stop_loop=True)
    async def setup_processes(self, at_start=True):
        # if at_start or self.wrapped_processes["MadMapper"].killed:
        #     wrapped_process = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'), "MadMapper", , dev_name="MadMapper")
        #     self.wrapped_processes["MadMapper"] = wrapped_process
        #     self.farm.RPC["MadMapper"] = await wrapped_process.start()
        #     # self.device_dict = await self.farm.RPC["MadMapper"].read_json()
        #     self.device_dict = await self.farm.RPC["MadMapper"].map_devices(True)
        #     log.info(f"\nResult of MadMapper.map_devices {self.device_dict}")
        #     if at_start:
        #         self.tasks.append(asyncio.create_task(wrapped_process.pinger(5)))
        #     else:
        #         log.info(f"Restarted Madmapper")

        for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
            if dev_params['Driver'] == 'PigletDriver':
                if at_start or not self.wrapped_processes[key].process.is_alive():
                    name = f"Piglet_{dev_params['Bank_ID']}"
                    wrapped_process = ProcessWrapper(PigletDriver, dev_params['RPC_Port'], name, dev_name=key)
                    await self.register_process(key,
                                                wrapped_process,
                                                name,
                                                2.0,
                                                at_start,
                                                port=dev_params['Path'],
                                                rpc_port=dev_params['RPC_Port'],
                                                baudrate=dev_params['Baudrate'],
                                                bank=dev_params['Bank_ID'])

        # for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
        #     if dev_params['Driver'] == 'PigletDriver':
        #         if at_start or self.wrapped_processes[key].killed:
        #             name = f"Piglet_{dev_params['Bank_ID']}"
        #             wrapped_process = ProcessWrapper(PigletDriver, dev_params['RPC_Port'], name, dev_name=key)
        #             self.wrapped_processes[key] = wrapped_process
        #             self.farm.RPC[name] = await wrapped_process.start(
        #                                                          port=dev_params['Path'],
        #                                                          rpc_port=dev_params['RPC_Port'],
        #                                                          baudrate=dev_params['Baudrate'])
        #             if at_start:
        #                 self.tasks.append(asyncio.create_task(wrapped_process.pinger(2)))
        #             else:
        #                 log.info(f"Restarted piglet driver: {key}")
        # elif dev_params['Driver'] == 'AlicatDriver':
        #     if at_start or self.wrapped_processes[key].killed:
        #         name = "MFC"
        #         wrapped_process = ProcessWrapper(AlicatDriver, dev_params['RPC_Port'], name, dev_name=key)
        #         self.wrapped_processes[key] = wrapped_process
        #         self.farm.RPC[name] = await wrapped_process.start(port=dev_params['Path'],
        #                                                           rpc_port=dev_params['RPC_Port'],
        #                                                           baudrate=dev_params['Baudrate'])
        #         if at_start:
        #             self.tasks.append(asyncio.create_task(wrapped_process.pinger(2)))
        #         else:
        #             log.info(f"Restarted Alicat driver: {key}")
        # elif dev_params['Driver'] == 'NumatoDriver':
        #     if at_start or self.wrapped_processes[key].killed:
        #         relay_id = dev_params['Numato_ID']
        #         name = f"Relay_{relay_id}"
        #         wrapped_process = ProcessWrapper(NumatoDriver, dev_params['RPC_Port'], name, dev_name=key)
        #         self.wrapped_processes[key] = wrapped_process
        #         self.farm.RPC[name] = await wrapped_process.start(device_port_name=dev_params['Path'],
        #                                                           rpc_server_port=dev_params['RPC_Port'])
        #         if at_start:
        #             self.tasks.append(asyncio.create_task(wrapped_process.pinger(2)))
        #         else:
        #             log.info(f"Restarted Numato driver: {key}")

        for key, dev_params in sorted(self.device_dict['Devices']['Network_Devices'].items()):
            if dev_params['Driver'] == 'IDriver':
                if at_start:
                    # Connect to existing RPC port
                    rpc_name = f"Picarro_{dev_params['SN']}"
                    self.farm.RPC[rpc_name] = AsyncWrapper(
                        CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{dev_params['RPC_Port']}", "PigssSupervisor"))
                # if at_start or not self.wrapped_processes[key].process.is_alive():
                #     name = f"Picarro_{dev_params['SN']}"
                #     wrapped_process = ProcessWrapper(PicarroAnalyzerDriver, dev_params['RPC_Port'], name, dev_name=key)
                #     chassis, analyzer = dev_params['SN'].split("-")
                #     await self.register_process(key,
                #                                 wrapped_process,
                #                                 name,
                #                                 2.0,
                #                                 at_start,
                #                                 instrument_ip_address=dev_params['IP'],
                #                                 database_writer=InfluxDBWriter(),
                #                                 rpc_server_port=dev_params['RPC_Port'],
                #                                 rpc_server_name=name,
                #                                 start_now=True,
                #                                 rpc_tunnel_config=self.rpc_tunnel_config,
                #                                 database_tags={
                #                                     "valve_pos": 0,
                #                                     "analyzer": analyzer,
                #                                     "chassis": chassis
                #                                 })
