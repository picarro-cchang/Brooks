#!/usr/bin/env python3
"""
Minimal simulation of the firmware on a piglet
"""
import asyncio
import random

import attr

from back_end.lologger.lologger_client import LOLoggerClient
from common.async_helper import log_async_exception

idstates = {"ambient", "flow_1", "flow_2", "flow_3", "calculate"}
opstates = {"standby", "identify", "control", "clean", "shutdown"}
log = LOLoggerClient(client_name=f"PigletSimulator", verbose=True)


@attr.s
class PigletSimulator:
    """
    The piglet_simulator is a software simulation of a piglet with a command line based interface.
    It consists of two co-routines cli() and fsm() which should be run concurrently. An input and output
    queue are used to simulate the serial port communication
    """
    bank = attr.ib(1)
    idstate = attr.ib("none")
    opstate = attr.ib("standby")
    sernum = attr.ib(65000)
    version = attr.ib("1.1.2")
    opstate_changed = attr.ib(factory=lambda: asyncio.Event())
    solenoid_state = attr.ib(factory=lambda: 8 * [0])
    bypass_values = attr.ib(factory=lambda: 8 * [0])
    BYPASS_ACTIVE = attr.ib(40000)
    active_chan = attr.ib(factory=lambda: 8 * [0])
    mfc_value = attr.ib(0)
    clean_solenoid_state = attr.ib(0)
    random_ids = attr.ib(0)

    def __attrs_post_init__(self):
        self.task = asyncio.create_task(self.fsm())
        log.info(f"Starting piglet simulator at bank {self.bank}")

    async def cli(self, command):
        atoms = command.upper().split()
        result = ""
        try:
            if atoms:
                result = "0"
                if atoms[0] == "*IDN?":
                    result = f"Picarro,Boxer,SN{self.sernum},{self.version}"
                elif atoms[0] == "ACTIVECH?":
                    code = int("".join([f"{i}" for i in reversed(self.active_chan)]), 2)
                    result = f"{code}"
                elif atoms[0] == "CHANENA":
                    sel = int(atoms[1]) - 1
                    assert 0 <= sel < 8
                    self.solenoid_state[sel] = 1
                elif atoms[0] == "CHANENA?":
                    sel = int(atoms[1]) - 1
                    assert 0 <= sel < 8
                    result = f"{self.solenoid_state[sel]}"
                elif atoms[0] == "CHANOFF":
                    sel = int(atoms[1]) - 1
                    assert 0 <= sel < 8
                    self.solenoid_state[sel] = 0
                elif atoms[0] == "CHANSET":
                    code = int(atoms[1])
                    self.solenoid_state = [1 if int(c) else 0 for c in reversed(format(code, '08b'))]
                    if self.opstate in ["standby", "clean"] and code != 0:
                        self.opstate = "control"
                        self.opstate_changed.set()
                    elif self.opstate in ["control"] and code == 0:
                        self.opstate = "standby"
                        self.opstate_changed.set()
                elif atoms[0] == "CHANSET?":
                    code = int("".join([f"{i}" for i in reversed(self.solenoid_state)]), 2)
                    result = f"{code}"
                elif atoms[0] == "MFCVAL?":
                    if (self.opstate in ["control", "clean", "reference"]):
                        self.mfc_value = random.randrange(10, 100)
                    elif self.opstate in ["identify"]:
                        if self.idstate in ["ambient", "calculate"]:
                            self.mfc_value = 0
                        elif self.idstate in ["flow_1"]:
                            self.mfc_value = 20
                        elif self.idstate in ["flow_2"]:
                            self.mfc_value = 30
                        elif self.idstate in ["flow_3"]:
                            self.mfc_value = 40
                    else:
                        self.mfc_value = 0
                    result = f"{self.mfc_value}"
                elif atoms[0] == "OPSTATE?":
                    result = f"{self.opstate}"
                elif atoms[0] == "IDSTATE?":
                    result = f"{self.idstate}"
                elif atoms[0] == "SERNUM":
                    self.sernum = int(atoms[1])
                elif atoms[0] == "SLOTID":
                    self.bank = int(atoms[1])
                elif atoms[0] == "SLOTID?":
                    result = f"{self.bank}"
                elif atoms[0] == "STANDBY":
                    if self.opstate in ("control", "clean"):
                        self.opstate = "standby"
                        self.opstate_changed.set()
                    else:
                        result = "-2"
                elif atoms[0] == "IDENTIFY":
                    if self.opstate in ("standby"):
                        self.opstate = "identify"
                        self.opstate_changed.set()
                    else:
                        result = "-2"
                elif atoms[0] == "CLEAN":
                    if self.opstate in ("control", "standby"):
                        self.opstate = "clean"
                        self.opstate_changed.set()
                    else:
                        result = "-2"
                elif atoms[0] == "SHUTDOWN":
                    if self.opstate in ("standby", "control", "clean", "identify"):
                        self.opstate = "shutdown"
                        self.opstate_changed.set()
                    else:
                        result = "-2"
                else:
                    result = "-1"
        # This is a developer tool, we are ok with a bare exception
        except Exception:  # noqa
            result = "-1"
        return result

    def shutdown(self):
        log.info(f"Stopping piglet simulator at bank {self.bank}")
        self.task.cancel()

    @log_async_exception(log_func=log.warning, stop_loop=True)
    async def fsm(self):
        self.opstate_changed.set()
        while True:
            await self.opstate_changed.wait()
            self.opstate_changed.clear()
            if self.opstate == "standby":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = self.BYPASS_ACTIVE
                self.clean_solenoid_state = 0
            elif self.opstate == "identify":
                self.idstate = "ambient"
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0.0
                self.clean_solenoid_state = 0
                await asyncio.sleep(1.0)
                self.idstate = "flow_1"
                await asyncio.sleep(1.5)
                self.idstate = "calculate"
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 1
                await asyncio.sleep(0.5)
                self.idstate = "none"
                self.opstate = "standby"
                for i, _ in enumerate(self.active_chan):
                    if self.random_ids:
                        self.active_chan[i] = 1 if random.uniform(0.0, 1.0) > 0.5 else 0
                    else:
                        self.active_chan[i] = i % 2
                self.opstate_changed.set()
            elif self.opstate == "clean":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = self.BYPASS_ACTIVE
                self.clean_solenoid_state = 1
