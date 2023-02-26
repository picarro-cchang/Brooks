from __future__ import print_function

from Host.autogen import interface
from Host.Common.CmdFIFO import CmdFIFOServerProxy
from Host.Common.SharedTypes import BROADCAST_PORT_RD_RECALC, RPC_PORT_DRIVER, RPC_PORT_SPECTRUM_COLLECTOR
from Host.Common.Listener import Listener
import numpy as np
import os
import Queue
import time

Driver = CmdFIFOServerProxy(
    "http://localhost:%d" % RPC_PORT_DRIVER,
    "PZTCal",
    IsDontCareConnection=False)

SpectrumCollector = CmdFIFOServerProxy(
    "http://localhost:%d" % RPC_PORT_SPECTRUM_COLLECTOR,
    "PZTCal",
    IsDontCareConnection=False)


def Log(msg):
    print(msg)

def main():
    rd_queue = Queue.Queue(3000)
    rdListener = Listener(queue=rd_queue,
                          port=BROADCAST_PORT_RD_RECALC,
                          elementType=interface.ProcessedRingdownEntryType,
                          retry=True,
                          name="PZTCal",
                          logFunc=Log)

    result_list_names = [
        "timestamp", "waveNumber", "waveNumberSetpoint", "angleSetpoint", "wlmAngle", "tunerValue", "pztValue", 
        "uncorrectedAbsorbance"
    ]
    results = {name: [] for name in result_list_names}
    wavenum = 6070.4
    vlaser_num = 1
    reps = 100
    dwell = 10
    subscheme_id = 100
    scheme_name = os.path.abspath("constant.sch")
    print(scheme_name)
    with open(scheme_name, "w") as sp:
        sp.write("%d  # Repetitions\n" % reps)
        sp.write("%d  # Scheme rows\n" % 1)
        sp.write("%.5f, %d, %d, %d\n" % (wavenum, dwell, subscheme_id, vlaser_num - 1))
    SpectrumCollector.stopScan()
    reg_vault = None
    try:
        reg_vault = Driver.saveRegValues([
            "PZT_OFFSET_VIRTUAL_LASER%d" % vlaser_num,
        ])

        schemes = [scheme_name]
        scheme_configs = {"": {"schemeCount": 1, "schemes": schemes}}
        SpectrumCollector.addNamedSchemeConfigsAsDicts("constant_scheme", scheme_configs)
        SpectrumCollector.setSequence("constant_scheme")

        pzt_val = 0
        Driver.wrDasReg("PZT_OFFSET_VIRTUAL_LASER%d" % vlaser_num, pzt_val)
        time.sleep(1.0)
        while True:
            try:
                rd_queue.get_nowait()
            except Queue.Empty:
                break
        SpectrumCollector.startScan()
        time.sleep(2.0)
        data = []
        while Driver.rdDasReg("SPECT_CNTRL_STATE_REGISTER") != 0:
            if len(data) % 100 == 0:
                pzt_val += 500
                if pzt_val >= 65536:
                    SpectrumCollector.stopScan()
                    break        
                if pzt_val % 1000 == 0:
                    print(pzt_val)
                Driver.wrDasReg(interface.PZT_OFFSET_VIRTUAL_LASER1, pzt_val)
            try:
                rddata = rd_queue.get(timeout=1.0)
                data.append(rddata)
            except Queue.Empty:
                print("Empty queue")
                continue
        # Keep getting data from the rd_queue until timeout
        while True:
            try:
                data.append(rd_queue.get(timeout=2.0))
            except Queue.Empty:
                break

        for datum in data:
            for fname in results:
                results[fname].append(getattr(datum, fname))   # Assemble the spectra from the contents of the queue

        # Convert lists to numpy arrays
        for fname in results:
            if fname == "timestamp":
                results[fname] = np.array(results[fname], dtype=np.int64)
                results[fname] = np.array(results[fname] - results[fname].min(), dtype=np.int32)
            else:
                results[fname] = np.array(results[fname], dtype=np.float32)

        np.savez_compressed("pzt_cal.npz", **results)
    finally:
        if reg_vault is not None:
            Driver.restoreRegValues(reg_vault)

if __name__ == "__main__":
    main()

