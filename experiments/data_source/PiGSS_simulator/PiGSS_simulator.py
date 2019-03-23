import datetime
import sys
from threading import Thread, Lock
import time
from collections import defaultdict, namedtuple
from heapq import heappop, heappush
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

from InfluxDBWriter import InfluxDBWriter
import numpy as np
import pytz

import CmdFIFO

ORIGIN = datetime.datetime(datetime.MINYEAR, 1, 1, 0, 0, 0, 0)
UNIXORIGIN = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)


def datetime_to_timestamp(t):
    td = t - ORIGIN
    return (td.days * 86400 + td.seconds) * 1000 + td.microseconds // 1000


def unix_time_to_timestamp(u):
    dt = UNIXORIGIN + datetime.timedelta(seconds=float(u))
    return datetime_to_timestamp(dt)


Analyzer = namedtuple('Analyzer', ['name', 'species', 'source', 'mode', 'interval'])
SimEvent = namedtuple('SimEvent', ['when', 'seq', 'gen'])


def scale_func(N, phi):
    sphi = np.sin(phi)
    return N*np.exp(-0.5*N*sphi**2)
    # return np.sin(N * phi) / sphi if abs(sphi) > 1.0e-12 else float(N)


class SimMeas(object):
    def __init__(self, species_name, num_pos, time_origin):
        # Set up the concentration profile for the species for each of the possible valve
        # positions. In this example, a profile is determined by a base concentration and
        # a fluctuation parameter. The concentration is specified by a circular sinc function
        # which remains close to the base concentration, but which rises to twice that value
        # at a time within the cycle which depends on the valve position.
        self.species_name = species_name
        # The following arrays define the profile parameters for the various valve positions
        self.base_conc = np.random.exponential(5.0, size=num_pos)
        self.fluct_conc = 0.01 * np.ones(num_pos)
        self.peak_phase = np.arange(num_pos, dtype=float) / num_pos  # Where in the cycle the peak occurs
        self.num_pos = num_pos
        self.cycle_time = 60.0 * num_pos**2
        self.time_origin = time_origin
        self.last_meas = None

    def get_conc(self, when, valve_pos):
        # Calculate concentration using a function 'scale_func'. The parameter N selects
        #  how sharp the peak is
        N = 10
        phase = np.pi * ((when - self.time_origin) / self.cycle_time - self.peak_phase[valve_pos])
        fac = 1.0 + scale_func(N, phase) / N
        return fac * self.base_conc[valve_pos] + np.random.normal(0.0, self.fluct_conc[valve_pos])

    def get_meas(self, when, valve_pos):
        # Use a low-pass filter to transition from one concentration level to the next
        #  The value of fac sets the rise and fall times for the analyzer
        fac = 0.3
        conc = self.get_conc(when, valve_pos)
        self.last_meas = conc if self.last_meas is None else fac * conc + (1.0 - fac) * self.last_meas
        return self.last_meas


class PiGSS(object):
    def __init__(self, analyzers, sim, num_pos=16, valve_period=60):
        self.data_queue = Queue()
        self.num_pos = num_pos
        self.valve_period = valve_period
        self.valve_pos = 0
        self.valve_lock = Lock()
        self.valve_mode = -1
        self.mean_conc = {}
        self.std_conc = {}
        self.sim_meas = {}
        self.analyzers = analyzers
        self.species = []
        self.running = True
        self.sim = sim
        start_time = sim.sim_time
        for analyzer in analyzers:
            for species in analyzer.species:
                self.sim_meas[species] = SimMeas(species, num_pos, start_time)
        self.last_valve_change_time = start_time
        self.results = defaultdict(list)

    def get_valve_mode(self):
        # If valve_mode == -1, we scan between the various valve positions in sequence
        #  and if valve_mode > 0, the valve position is fixed to that value
        return self.valve_mode

    def set_valve_mode(self, mode):
        if mode < -1 or mode >= self.num_pos:
            raise ValueError("Invalid valve mode")
        with self.valve_lock:
            if mode != self.valve_mode:
                self.valve_mode = mode
                if mode >= 0:  # Switch to fixed valve position
                    self.valve_pos = mode
                    self.last_valve_change_time = time.time()
                    print('Manual valve set %.3f: valve_position %d' % (self.last_valve_change_time, self.valve_pos))
                else:  # (Re-)start the valve switcher task
                    self.valve_pos = (self.valve_pos + 1) % self.num_pos
                    self.last_valve_change_time = time.time()
                    self.sim.enqueue_task(self.sim.sim_time, self.valve_switcher_task())

    def valve_switcher_task(self):
        period = self.valve_period
        sim = self.sim
        name = 'Valve switcher'
        while True:
            print('%s running at %.3f: valve_position %d' % (name, sim.sim_time, self.valve_pos))
            yield sim.sim_time + period
            with self.valve_lock:
                if self.valve_mode >= 0:
                    yield None
                self.valve_pos += 1
                if self.valve_pos >= self.num_pos:
                    self.valve_pos = 0
                self.last_valve_change_time = sim.sim_time

    def calc_data_task(self, analyzer):
        sim = self.sim
        filling = True
        queue_hwm = 300
        queue_lwm = 50
        while True:
            measurements = []
            for species in analyzer.species:
                meas = self.sim_meas[species].get_meas(sim.sim_time, self.valve_pos)
                # print('Measuring %s at %.3f: %.3f' % (species, sim.sim_time, meas))
                measurements.append(meas)
                self.results[species].append((sim.sim_time, meas))
            dm_dict = self.make_data_manager_dict(sim.sim_time, analyzer, measurements)
            # Add information about valve position and time since last change
            dm_dict['valve_pos'] = self.valve_pos
            dm_dict['data']['valve_stable_time'] = sim.sim_time - self.last_valve_change_time
            # while True:
            #     qsize = self.data_queue.qsize()
            #     if filling and qsize > queue_hwm:
            #         filling = False
            #     elif not filling and qsize < queue_lwm:
            #         filling = True
            #     if filling:
            #         self.data_queue.put((analyzer.name, dm_dict))
            #         break
            #     else:
            #         time.sleep(0.05)
            self.data_queue.put((analyzer.name, dm_dict))
            yield sim.sim_time + analyzer.interval

    def make_data_manager_dict(self, unix_time, analyzer, measurements):
        result = {'time': unix_time,
                  'source': analyzer.source,
                  'mode': analyzer.mode,
                  'good': 1,
                  'data': {}}
        for species, measurement in zip(analyzer.species, measurements):
            result['data'][species] = measurement
        return result

    def data_gen(self):
        tag_list = ['source', 'mode', 'ver', 'good', 'valve_pos']
        while True:
            try:
                analyzer_name, obj = self.data_queue.get(timeout=5.0)
                data = {'measurement': 'crds', 'fields': {}, 'tags': {'analyzer': analyzer_name}}
                if 'time' in obj:
                    data['time'] = datetime.datetime.fromtimestamp(obj['time'], tz=pytz.utc)
                for tag in tag_list:
                    if tag in obj:
                        data['tags'][tag] = obj[tag]
                for field in obj['data']:
                    data['fields'][field] = obj['data'][field]
                yield data
            except Empty:
                if self.running:
                    yield None
                else:
                    raise StopIteration


class Simulator(object):
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
            next_time = next(gen)
            if next_time is not None:
                self.enqueue_task(next_time, gen)
        print("Simulation complete")

def printer(x):
    print(x)
    return x

def main():
    db_writer = InfluxDBWriter("localhost", "pigss_data", batch_size=500)
    sim = Simulator(real_time=True)
    num_pos = 16
    sim.sim_time = time.time() - 2 * 60 * num_pos**2
    analyzers = [
        Analyzer('AMADS3001', ['NH3', 'HF'], 'analyze_AMADS_LCT', 'AMADS_LCT_mode', 1.1),
        Analyzer('SBDS3002', ['HCl'], 'analyze_SADS', 'HCl_mode', 1.2),
        Analyzer('BFADS3003', ['H2S'], 'analyze_BFADS', 'BFADS_mode', 1.3)]

    pigss = PiGSS(analyzers, sim, num_pos, valve_period=60)
    if pigss.valve_mode < 0:
        sim.enqueue_task(sim.sim_time, pigss.valve_switcher_task())
    for analyzer in analyzers:
        sim.enqueue_task(sim.sim_time, pigss.calc_data_task(analyzer))
    # sim.enqueue_task(sim.sim_time + 2 * 60 * num_pos**2, sim.stop_task())

    rpcServer = CmdFIFO.CmdFIFOServer(("", 51234),
                                      ServerName="RPCHost",
                                      ServerDescription="RpcHost",
                                      ServerVersion="1.0",
                                      threaded=True)

    def rpc_task():
        rpcServer.serve_forever()
        sim.stop()

    rpcServer.register_function(printer)
    rpcServer.register_function(pigss.set_valve_mode)
    rpcServer.register_function(pigss.get_valve_mode)

    rpc_thread = Thread(target=rpc_task)
    rpc_thread.daemon = True
    rpc_thread.start()

    th = Thread(target=db_writer.run, args=(pigss.data_gen,))
    th.daemon = True
    th.start()
    sim.run()
    pigss.running = False
    print("Waiting for sending to database to complete")
    th.join()

if __name__ == "__main__":
    main()

    # for species in pigss.results:
    #     plt.figure()
    #     when = np.asarray([t for t, _ in pigss.results[species]])
    #     conc = np.asarray([c for _, c in pigss.results[species]])
    #     plt.plot(when, conc)
    #     plt.grid(True)
    #     plt.title(species)
    # plt.show()
