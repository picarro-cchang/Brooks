#!/usr/bin/env python3
"""
Rudimentary analyzer simulator which provides an interface resembling that of
 a PicarroAnalyzerDriver. Sinusoidal concentration variations with random
 amplitude, frequency and background corrupted by white Gaussian noise at
 each of several ports are simulated
"""
import json
import time
from collections import namedtuple
from heapq import heappop, heappush
from threading import Thread

import attr
import click
import numpy as np
from setproctitle import setproctitle

from common.broadcaster import Broadcaster
from common.CmdFIFO import CmdFIFOServer, CmdFIFOServerProxy
from common.string_pickler import pack_arbitrary_object
from common.timeutils import get_timestamp

RPC_PORT_DRIVER = 50010
RPC_PORT_SUPERVISOR = 50030
RPC_PORT_INSTR_MANAGER = 50110
BROADCAST_PORT_DATA_MANAGER = 40060


@attr.s
class Analyzer:
    chassis = attr.ib(type=str)
    analyzer = attr.ib(type=str)
    analyzer_num = attr.ib(type=str)
    species = attr.ib()
    source = attr.ib(type=str)
    mode = attr.ib(type=str)
    interval = attr.ib(type=float)
    seed = attr.ib(type=int, default=98765)


SimEvent = namedtuple('SimEvent', ['when', 'seq', 'gen'])


class Simulator(object):
    # Simple generator-based simulator which schedules "events" at specified times
    # Each event has an associated generator function "task" which performs the action
    #  associated with that event and (possibly) enqueues additional events before
    #  yielding, ready to be run when it is scheduled again.
    #
    # Simulation can take place in real time or events can be dispatched as soon as they
    #  reach the head of the scheduler queue (which is organized as a priority queue
    #  ordered by time)
    def __init__(self, real_time=False):
        self.next_seq = 0
        self.event_heap = []
        self.running = False
        self.real_time = real_time
        self.sim_time = time.time() if real_time else 0

    def enqueue_task(self, when, task):
        heappush(self.event_heap, SimEvent(when, self.next_seq, task))
        self.next_seq += 1

    def stop(self):
        self.running = False

    def stop_task(self):
        self.stop()
        yield None

    def run(self):
        self.running = True
        while self.running and len(self.event_heap) > 0:
            if self.real_time:
                when = self.event_heap[0].when
                wait_time = when - time.time()
                if wait_time > 0:
                    time.sleep(wait_time)
            event = heappop(self.event_heap)
            self.sim_time, seq, gen = event
            next_time = next(gen)  # This runs the task for the event
            if next_time is not None:
                self.enqueue_task(next_time, gen)


class SimMeas(object):
    def __init__(self, species_name, num_pos, time_origin):
        # Set up the concentration profile for the species for each of the possible valve
        # positions. In this example, a profile is determined by a base concentration and
        # a fluctuation parameter. The concentration is specified by a circular sinc function
        # which remains close to the base concentration, but which rises to twice that value
        # at a time within the cycle which depends on the valve position.
        self.num_pos = num_pos
        self.species_name = species_name
        self.switching_interval = 60.0
        # The following arrays define the profile parameters for the various valve positions
        self.ampl = np.random.exponential(5.0, size=num_pos)
        self.mean = np.random.uniform(low=1.0, high=3.0, size=num_pos) * self.ampl
        self.period = np.random.uniform(low=5.0 * num_pos * self.switching_interval,
                                        high=10.0 * num_pos * self.switching_interval,
                                        size=num_pos)
        self.time_origin = time_origin - self.period * np.random.uniform(low=0.0, high=1.0, size=num_pos)
        self.fluct_conc = 0.01 * np.ones(num_pos)
        self.last_meas = None

    def get_conc(self, when, valve_pos):
        # Calculate concentration using sinusoidal model
        phase = 2 * np.pi * (when - self.time_origin[valve_pos - 1]) / self.period[valve_pos - 1]
        noise = np.random.normal(0.0, self.fluct_conc[valve_pos - 1])
        return self.mean[valve_pos - 1] + self.ampl[valve_pos - 1] * np.cos(phase) + noise

    def get_meas(self, when, valve_pos):
        # Use a low-pass filter to transition from one concentration level to the next
        #  The value of fac sets the rise and fall times for the analyzer
        fac = 0.3
        conc = self.get_conc(when, valve_pos) if 1 <= valve_pos <= self.num_pos else 0.0
        self.last_meas = conc if self.last_meas is None else fac * conc + (1.0 - fac) * self.last_meas
        return self.last_meas


class Driver:
    def __init__(self, sim, analyzer, ip_address):
        self.ip_address = ip_address
        self.rpc_server = CmdFIFOServer((f"{ip_address}", RPC_PORT_DRIVER), ServerName="PicarroDriverSimulator", threaded=True)
        self.register_rpc_functions()
        self.sim = sim
        self.analyzer = analyzer
        np.random.seed(seed=analyzer.seed)
        time_origin = time.time()
        self.sim_meas = {species: SimMeas(species, 32, time_origin) for species in self.analyzer.species}
        self.sim.enqueue_task(time_origin + analyzer.interval, self.calc_data_task(analyzer))
        self.valve_pos = 13

    def allVersions(self):
        versionDict = {}
        versionDict["interface"] = 1
        versionDict["host release"] = "Simulation"
        versionDict["host version id"] = 1
        versionDict["host version no"] = 2
        versionDict["src version id"] = 3
        versionDict["src version no"] = 4
        return versionDict

    def fetchHardwareCapabilities(self):
        # TODO: Make this more dynamic
        return {"Ethane": False, "iGPS": False, "iCH4": False, "Mast": False}

    def fetchLogicEEPROM(self):
        return [dict(Chassis=self.analyzer.chassis, Analyzer=self.analyzer.analyzer, AnalyzerNum=self.analyzer.analyzer_num)]

    def dasGetTicks(self):
        return get_timestamp()

    def hostGetTicks(self):
        return get_timestamp()

    def setValveMask(self, mask):
        self.valve_pos = mask

    def getValveMask(self):
        return self.valve_pos

    def register_rpc_functions(self):
        # TODO: Implement non-existent RPC functions
        self.rpc_server.register_function(self.allVersions)
        self.rpc_server.register_function(self.dasGetTicks)
        self.rpc_server.register_function(self.fetchHardwareCapabilities)
        self.rpc_server.register_function(self.fetchLogicEEPROM)
        # self.rpc_server.register_function(self.getLockStatus)
        # self.rpc_server.register_function(self.getPressureReading)
        # self.rpc_server.register_function(self.getProportionalValves)
        self.rpc_server.register_function(self.getValveMask)
        # self.rpc_server.register_function(self.getWarmingState)
        self.rpc_server.register_function(self.hostGetTicks)
        # self.rpc_server.register_function(self.invokeSupervisorLauncher)
        # self.rpc_server.register_function(self.rdDasReg)
        # self.rpc_server.register_function(self.rdFPGA)
        self.rpc_server.register_function(self.setValveMask)
        # self.rpc_server.register_function(self.startEngine)
        # self.rpc_server.register_function(self.wrDasReg)
        # self.rpc_server.register_function(self.wrFPGA)

    def make_data_manager_dict(self, unix_time, analyzer, measurements):
        result = {'time': unix_time, 'source': analyzer.source, 'mode': analyzer.mode, 'good': 1, 'data': {}}
        for species, measurement in zip(analyzer.species, measurements):
            result['data'][species] = measurement
        return result

    def calc_data_task(self, analyzer):
        sim = self.sim
        dm_broadcaster = Broadcaster(BROADCAST_PORT_DATA_MANAGER, self.ip_address)
        while True:
            measurements = []
            for species in analyzer.species:
                meas = self.sim_meas[species].get_meas(sim.sim_time, self.valve_pos)
                measurements.append(meas)
            dm_dict = self.make_data_manager_dict(sim.sim_time, analyzer, measurements)
            dm_broadcaster.send(pack_arbitrary_object(dm_dict))
            yield sim.sim_time + analyzer.interval


class Supervisor:
    def __init__(self, sim, analyzer, ip_address='localhost'):
        self.ip_address = ip_address
        self.rpc_server = CmdFIFOServer((f"{ip_address}", RPC_PORT_SUPERVISOR),
                                        ServerName="PicarroSupervisorSimulator",
                                        threaded=True)
        self.sim = sim
        self.analyzer = analyzer
        self.register_rpc_functions()
        self.start_applications()

    def start_applications(self):
        Thread(target=Driver(self.sim, self.analyzer, self.ip_address).rpc_server.serve_forever, daemon=True).start()
        Thread(target=InstMgr(self.sim, self.ip_address).rpc_server.serve_forever, daemon=True).start()
        self.Driver = CmdFIFOServerProxy(f"http://{self.ip_address}:{RPC_PORT_DRIVER}", "From Supervisor")
        self.InstMgr = CmdFIFOServerProxy(f"http://{self.ip_address}:{RPC_PORT_INSTR_MANAGER}", "From Supervisor")

    def RPC_TerminateApplications(self):
        self.Driver.CmdFIFO.StopServer()
        self.InstMgr.CmdFIFO.StopServer()
        self.rpc_server.Stop()

    def register_rpc_functions(self):
        self.rpc_server.register_function(self.RPC_TerminateApplications)


class InstMgr:
    def __init__(self, sim, ip_address):
        self.rpc_server = CmdFIFOServer((f"{ip_address}", RPC_PORT_INSTR_MANAGER),
                                        ServerName="PicarroInstMgrSimulator",
                                        threaded=True)
        self.sim = sim
        self.Supervisor = CmdFIFOServerProxy(f"http://{ip_address}:{RPC_PORT_SUPERVISOR}", "From InstMgr")
        self.register_rpc_functions()

    def INSTMGR_ShutdownRpc(self):
        self.Supervisor.RPC_TerminateApplications()

    def register_rpc_functions(self):
        # TODO: Implement non-existent RPC functions
        # self.rpc_server.register_function(self.INSTMGR_GetStateRpc)
        # self.rpc_server.register_function(self.INSTMGR_GetStatusRpc)
        self.rpc_server.register_function(self.INSTMGR_ShutdownRpc)


def get_analyzer_details(params):
    d = {}
    for f in attr.fields(Analyzer):
        if f.name in params:
            d[f.name] = params[f.name] if f.type is None else f.type(params[f.name])
    return Analyzer(**d)


class AnalyzerSimulator:
    def __init__(self, rpc_port, analyzer):
        self.ip_address = analyzer["ip_address"]
        self.analyzer = get_analyzer_details(analyzer)

        sim = Simulator(real_time=True)
        supervisor = Supervisor(sim, self.analyzer, self.ip_address)

        self.rpc_server = CmdFIFOServer(("", rpc_port),
                                        ServerName=f"AnalyzerSimulator on {self.ip_address}",
                                        ServerDescription="Run analyzer simulator",
                                        threaded=True)

        def supervisor_rpc_task():
            supervisor.rpc_server.serve_forever()
            sim.stop()
            self.rpc_server.Stop()

        Thread(target=supervisor_rpc_task, daemon=True).start()
        Thread(target=sim.run, daemon=True).start()
        self.rpc_server.serve_forever()


@click.command()
@click.argument("proc_name")
@click.argument("analyzer_json")
@click.argument("ip_address")
def main(proc_name, analyzer_json, ip_address):
    if proc_name:
        setproctitle(f"python Simulation on {proc_name}")

    sim = Simulator(real_time=True)
    supervisor = Supervisor(sim, Analyzer(**json.loads(analyzer_json)), ip_address)

    def supervisor_rpc_task():
        supervisor.rpc_server.serve_forever()
        sim.stop()

    Thread(target=supervisor_rpc_task, daemon=True).start()
    sim.run()


if __name__ == "__main__":
    main()
