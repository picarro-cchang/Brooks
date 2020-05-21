#!/usr/bin/env python3
"""
Hierarchical state machine which supervises processes (typically drivers and
 services) which are run during the operation of the sampler rack and starts
 up their RPC servers. Monitoring tasks that ping these processes through their
 RPC servers are also started. These monitors will restart those processes
 which fail to respond to pings.
"""
import asyncio
import json
import time
from collections import deque

import attr
from aiomultiprocess import Process
from setproctitle import setproctitle

from async_hsm import Ahsm, Event, Framework, Signal, TimeEvent, state
from back_end.analyzer_driver.picarro_analyzer_driver import \
    PicarroAnalyzerDriver
from back_end.database_access.influx_database import InfluxDBWriter
from back_end.influxdb_retention.db_decimator import DBDecimatorFactory
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.madmapper.madmapper import MadMapper
from back_end.mfc_driver.alicat.alicat_driver import AlicatDriver
from back_end.piglet.piglet_driver import PigletDriver
from back_end.relay_driver.numato.numato_driver import NumatoDriver
from back_end.state_machines.pigss_payloads import SystemConfiguration
from back_end.time_synchronization.setup_timesync_client import \
    time_sync_analyzers
from common import CmdFIFO
from common.async_helper import log_async_exception
from common.rpc_ports import rpc_ports
from simulation.analyzer_simulator import AnalyzerSimulator
from simulation.sim_alicat_driver import SimAlicatDriver
from simulation.sim_numato_driver import SimNumatoDriver
from simulation.sim_piglet_driver import SimPigletDriver

port = rpc_ports.get('madmapper')
ping_interval = 2.0

log = LOLoggerClient(client_name="AppSupervisor", verbose=True)


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
    daemonic = attr.ib(True)

    async def start_driver(self, *args, **kwargs):
        setproctitle(f"python Supervised {self.name}")
        d = self.driver(*args, **kwargs)
        if hasattr(d, "rpc_serve_forever"):
            d.rpc_serve_forever()

    async def start(self, *args, **kwargs):
        if self.process is not None and self.process.is_alive():
            self.process.kill()
            await self.process.join()
        log.info(f"Starting process {self.name}.")
        self.start_time = time.time()
        self.process = Process(target=self.start_driver, args=args, kwargs=kwargs)
        self.process.daemon = self.daemonic
        self.process.start()
        setproctitle("python aiomultiprocess support")
        self.rpc_raw = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{self.rpc_port}", "PigssSupervisor")
        self.rpc_wrapper = AsyncWrapper(self.rpc_raw)
        await asyncio.sleep(1.0)
        return self.rpc_wrapper

    async def stop_process(self, stop_reason="Unknown"):
        if self.process.is_alive():
            self.process.kill()
        if self.stop_time is None:
            self.stop_time = time.time()
            self.stop_reason = stop_reason
        await self.process.join()

    @log_async_exception(log_func=log.warning)
    async def pinger(self, period):
        try:
            while True:
                await asyncio.sleep(period)
                if await asyncio.wait_for(self.rpc_wrapper.CmdFIFO.PingFIFO(), timeout=2 * period) != 'Ping OK':
                    raise ValueError("Bad response to ping")
        except CmdFIFO.RemoteException:
            log.warning(f"Ping to process {self.name} raised exception. Killing process.")
            await self.stop_process("Ping to process raised exception.")
        except asyncio.TimeoutError:
            log.warning(f"Ping to process {self.name} timed out. Killing process.")
            await self.stop_process("Ping to process timed out.")
        except ValueError:
            log.warning(f"Ping to process {self.name} returned unexpected response. Killing process.")
            await self.stop_process("Ping to process returned unexpected response.")


class PigssSupervisor(Ahsm):
    def __init__(self, farm=None):
        log.debug("Starting PigssSupervisor")
        super().__init__()
        self.farm = farm
        self.simulation = self.farm.config.get_simulation_enabled()
        self.random_ids = self.farm.config.get_simulation_random_ids()
        self.tunnel_config_filename = self.farm.config.get_rpc_tunnel_config_filename()
        self.farm.RPC = {}
        self.wrapped_processes = {}  # List of Process objects
        self.tasks = []
        self.device_dict = {}
        self.bank_list = []
        self.service_list = []
        self.old_processes = deque(maxlen=32)
        self.te = TimeEvent("MONITOR_PROCESSES")
        self.mon_task = None
        with open(self.tunnel_config_filename, "r") as f:
            self.rpc_tunnel_config = json.loads(f.read())
            log.debug(f"RPC Tunnel settings loaded from {self.tunnel_config_filename}")

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
        self.publish_errors = True
        Framework.subscribe("ERROR", self)
        Framework.subscribe("SERVICES_STARTED", self)
        Framework.subscribe("MADMAPPER_DONE", self)
        Framework.subscribe("DRIVERS_STARTED", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("TERMINATE", self)
        Framework.subscribe("PROCESSES_MONITORED", self)
        return self.tran(self._operational)

    @state
    def _exit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.terminated = True
            return self.handled(e)
        elif sig == Signal.TERMINATE:
            return self.handled(e)
        return self.super(self.top)

    @state
    def _operational(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._startup)
        elif sig == Signal.EXIT:
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            for wrapper in self.wrapped_processes.values():
                if wrapper.process is not None:
                    wrapper.process.kill()
        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)
        return self.super(self.top)

    @state
    def _startup(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.service_list = self.farm.config.get_services()
            if self.farm.config.get_simulation_enabled():
                for i, simulator in enumerate(self.farm.config.get_simulation_analyzers()):
                    self.service_list.append({
                        'Name': f'AnalyzerSimulator_{i+1}',
                        'RPC_Port': rpc_ports.get('analyzer_simulator_base') + i,
                        'Parameters': {
                            "analyzer": simulator
                        }
                    })
            self.tasks.append(self.run_async(self.startup_services()))
            return self.handled(e)
        elif sig == Signal.SERVICES_STARTED:
            self.tasks.append(self.run_async(self.perform_mapping()))
            return self.handled(e)
        elif sig == Signal.MADMAPPER_DONE:
            payload = e.value
            self.device_dict = payload.copy()
            self.bank_list = []
            for descr in payload["Devices"]["Serial_Devices"].values():
                if descr["Driver"] == "PigletDriver":
                    self.bank_list.append(descr["Bank_ID"])
            self.tasks.append(self.run_async(self.startup_drivers()))
            return self.handled(e)
        elif sig == Signal.DRIVERS_STARTED:
            Framework.publish(
                Event(Signal.SYSTEM_CONFIGURE,
                      SystemConfiguration(bank_list=sorted(self.bank_list), mad_mapper_result=self.device_dict)))
            return self.tran(self._supervising)
        return self.super(self._operational)

    @state
    def _supervising(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            # TODO: Change to a symbolic constant
            self.te.postIn(self, 2 * ping_interval)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.te.disarm()
            return self.handled(e)
        elif sig == Signal.SYSTEM_CONFIGURE:
            log.info(f"System config: {e.value}")
            startup_plan = self.farm.config.get_startup_plan()
            if startup_plan is not None and not self.farm.config.get_wait_warmup():
                self.run_async(self.farm.controller.auto_setup_flow(startup_plan))
            return self.handled(e)
        elif sig == Signal.MONITOR_PROCESSES:
            self.mon_task = self.run_async(self.monitor_processes())
            self.tasks.append(self.mon_task)
            return self.handled(e)
        elif sig == Signal.PROCESSES_MONITORED:
            self.tasks.remove(self.mon_task)
            self.te.postIn(self, 2 * ping_interval)
            return self.handled(e)
        return self.super(self._operational)

    async def reconfigure(self, delay):
        await asyncio.sleep(delay)
        Framework.publish(
            Event(Signal.SYSTEM_CONFIGURE, SystemConfiguration(bank_list=sorted(self.bank_list),
                                                               mad_mapper_result=self.device_dict)))

    @log_async_exception(log_func=log.error, publish_terminate=True)
    async def perform_mapping(self):
        # Run the MadMapper after a specified delay
        delay = self.farm.config.get_madmapper_startup_delay()
        log.info(f"\nWaiting {delay} seconds before starting madmapper.")
        await asyncio.sleep(delay)
        wrapped_process = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'), "MadMapper")
        self.wrapped_processes["MadMapper"] = wrapped_process
        madmapper_rpc = await wrapped_process.start(simulation=self.simulation)
        self.device_dict = await madmapper_rpc.map_devices(True)
        log.debug(f"\nResult of MadMapper.map_devices {self.device_dict}")
        Framework.publish(Event(Signal.MADMAPPER_DONE, self.device_dict))
        # Once done, stop the process
        await madmapper_rpc.CmdFIFO.StopServer()
        await wrapped_process.stop_process("Device mapping complete")

    async def register_process(self, key, wrapped_process, rpc_name, ping_interval, at_start, **process_kwargs):
        """Store the `wrapped_process` in the wrapped_processes dictionary under the keyname `key`, archiving
            any process already there into `old_processes`. This `wrapped_process` contains a Driver with an
            RPC server which is registered with the farm under the name `rpc_name`. If this is the first time
            that this is run for a process, `at_start` is True, and we also start a ping process to check the
            health of the RPC server every `ping_interval` seconds. When the Driver is constructed, it is passed
            ``process_kwargs`` as its arguments.
        """
        if key in self.wrapped_processes:
            await self.wrapped_processes[key].stop_process("Found dead by process monitor")
            self.old_processes.append(self.wrapped_processes[key])
        self.wrapped_processes[key] = wrapped_process
        self.farm.RPC[rpc_name] = await wrapped_process.start(**process_kwargs)
        if at_start:
            # Try to send the first ping and kill the system if there is no response
            #  within a certain interval
            start_ok = True
            err_msg = ""
            try:
                if await asyncio.wait_for(wrapped_process.rpc_wrapper.CmdFIFO.PingFIFO(), timeout=2 * ping_interval) != 'Ping OK':
                    raise ValueError("Bad response to ping")
            except CmdFIFO.RemoteException as e:
                start_ok = False
                err_msg = repr(e)
            except asyncio.TimeoutError as e:
                start_ok = False
                err_msg = repr(e)
            except ValueError as e:
                start_ok = False
                err_msg = repr(e)
            if start_ok:
                self.tasks.append(self.run_async(wrapped_process.pinger(ping_interval)))
            else:
                log.error(f"Cannot start {wrapped_process.name}, aborting due to {err_msg}. Check configuration information.")
                Framework.publish(Event(Signal.TERMINATE, None))
                return
        else:
            name = wrapped_process.driver.__name__
            if "PigletDriver" in name:
                self.run_async(self.reconfigure(10.0))
                log.debug(f"Restarted {name} at {key}. Recovery and reconfiguration scheduled.")
                log.info(f"Restarted process. Recovery and reconfiguration scheduled.")
            else:
                log.debug(f"Restarted {name} at {key}")
                log.info(f"Restarted process.")
        return

    async def setup_drivers(self, at_start=True):
        db_config = self.farm.config.get_time_series_database()
        use_sim_ui = self.farm.config.get_simulation_ui_enabled()
        for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
            if dev_params['Driver'] == 'PigletDriver':
                if at_start or not self.wrapped_processes[key].process.is_alive():
                    name = f"Piglet_{dev_params['Bank_ID']}"
                    DriverClass = SimPigletDriver if self.simulation else PigletDriver
                    kwextra = {}
                    if self.simulation:
                        kwextra["enable_ui"] = use_sim_ui
                    wrapped_process = ProcessWrapper(DriverClass, dev_params['RPC_Port'], name, dev_name=key)
                    await self.register_process(key,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                port=dev_params['Path'],
                                                rpc_port=dev_params['RPC_Port'],
                                                baudrate=dev_params['Baudrate'],
                                                bank=dev_params['Bank_ID'],
                                                random_ids=self.random_ids,
                                                **kwextra)
            elif dev_params['Driver'] == 'AlicatDriver':
                if at_start or not self.wrapped_processes[key].process.is_alive():
                    name = "MFC"
                    DriverClass = SimAlicatDriver if self.simulation else AlicatDriver
                    kwextra = {}
                    if self.simulation:
                        kwextra["enable_ui"] = use_sim_ui
                    wrapped_process = ProcessWrapper(DriverClass, dev_params['RPC_Port'], name, dev_name=key)
                    await self.register_process(key,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                port=dev_params['Path'],
                                                rpc_port=dev_params['RPC_Port'],
                                                baudrate=dev_params['Baudrate'],
                                                **kwextra)
            elif dev_params['Driver'] == 'NumatoDriver':
                if at_start or not self.wrapped_processes[key].process.is_alive():
                    relay_id = dev_params['Numato_ID']
                    name = f"Relay_{relay_id}"
                    DriverClass = SimNumatoDriver if self.simulation else NumatoDriver
                    kwextra = {}
                    if self.simulation:
                        kwextra["enable_ui"] = use_sim_ui
                    wrapped_process = ProcessWrapper(DriverClass, dev_params['RPC_Port'], name, dev_name=key)
                    await self.register_process(key,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                device_port_name=dev_params['Path'],
                                                rpc_server_port=dev_params['RPC_Port'],
                                                **kwextra)

        for key, dev_params in sorted(self.device_dict['Devices']['Network_Devices'].items()):
            if dev_params['Driver'] == 'IDriver':
                if at_start or not self.wrapped_processes[key].process.is_alive():
                    name = f"Picarro_{dev_params['SN']}"
                    wrapped_process = ProcessWrapper(PicarroAnalyzerDriver, dev_params['RPC_Port'], name, dev_name=key)
                    chassis, analyzer = dev_params['SN'].split("-")
                    await self.register_process(key,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                instrument_ip_address=dev_params['IP'],
                                                database_writer=InfluxDBWriter(address=db_config["server"],
                                                                               db_port=db_config["port"],
                                                                               db_name=db_config["name"]),
                                                rpc_server_port=dev_params['RPC_Port'],
                                                rpc_server_name=name,
                                                start_now=True,
                                                rpc_tunnel_config=self.rpc_tunnel_config,
                                                database_tags={
                                                    "valve_pos": 0,
                                                    "analyzer": analyzer,
                                                    "chassis": chassis
                                                })

    async def setup_services(self, at_start=True):
        db_config = self.farm.config.get_time_series_database()
        for service in self.service_list:
            name = service["Name"]
            if name == "DBDecimator":
                if at_start or not self.wrapped_processes[name].process.is_alive():

                    def DBDecimator(**k):
                        return DBDecimatorFactory().create_DBDecimator_with_settings(k)

                    rpc_port = service["RPC_Port"]
                    wrapped_process = ProcessWrapper(DBDecimator, rpc_port, name, dev_name="Service")
                    params = {
                        **dict(db_host_address=db_config["server"], db_port=db_config["port"], db_name=db_config["name"]),
                        **service.get("Parameters", {})
                    }
                    await self.register_process(name,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                rpc_server_port=rpc_port,
                                                **params)
            elif name.startswith("AnalyzerSimulator"):
                if at_start or not self.wrapped_processes[name].process.is_alive():
                    rpc_port = service["RPC_Port"]
                    wrapped_process = ProcessWrapper(AnalyzerSimulator, rpc_port, name, dev_name="Service")
                    await self.register_process(name,
                                                wrapped_process,
                                                name,
                                                ping_interval,
                                                at_start,
                                                rpc_port=rpc_port,
                                                **service.get("Parameters", {}))
            else:
                raise ValueError(f"Unknown service {name}. Terminating.")

    @log_async_exception(log_func=log.warning, publish_terminate=True)
    async def startup_services(self):
        await self.setup_services(at_start=True)
        await asyncio.sleep(1.0)
        Framework.publish(Event(Signal.SERVICES_STARTED, None))

    @log_async_exception(log_func=log.warning, publish_terminate=True)
    async def startup_drivers(self):
        if not self.simulation:
            picarro_analyzer_ips = [
                device["IP"] for device in self.device_dict["Devices"]["Network_Devices"].values() if device["Driver"] == "IDriver"
            ]
            await time_sync_analyzers(picarro_analyzer_ips)
        await self.setup_drivers(at_start=True)
        Framework.publish(Event(Signal.DRIVERS_STARTED, None))

    @log_async_exception(log_func=log.warning)
    async def monitor_processes(self):
        await self.setup_services(at_start=False)
        await self.setup_drivers(at_start=False)
        Framework.publish(Event(Signal.PROCESSES_MONITORED, None))
