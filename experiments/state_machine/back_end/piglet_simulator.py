"""
The piglet_simulator is a software simulation of a piglet with a command line based interface.
It consists of two co-routines cli() and fsm() which should be run concurrently. An input and output
queue are used to simulate the serial port communication
"""
import asyncio
import random
import time

import attr

opstates = {"power_up", "standby", "ident", "ident_2", "sampling", "clean", "reference", "fault", "power_off"}


@attr.s
class PigletSimulator:
    bank = attr.ib(1)
    opstate = attr.ib("power_off")
    sernum = attr.ib(65000)
    version = attr.ib("1.0.3")
    opstate_changed = attr.ib(factory=lambda: asyncio.Event())
    solenoid_state = attr.ib(factory=lambda: 8 * [0])
    bypass_values = attr.ib(factory=lambda: 8 * [0])
    BYPASS_ACTIVE = attr.ib(40000)
    active_chan = attr.ib(factory=lambda: 8 * [0])
    mfc_value = attr.ib(0)
    clean_solenoid_state = attr.ib(0)

    async def cli(self, command):
        atoms = command.upper().split()
        result = ""
        try:
            if atoms:
                result = "0"
                if atoms[0] == "*IDN?":
                    result = f"Picarro,Boxer,SN{self.sernum},{self.version}"
                elif atoms[0] == "CHANAVAIL?":
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
                    self.solenoid_state = [1 if int(c) else 0 for c in reversed(format(int(atoms[1]), '08b'))]
                elif atoms[0] == "CHANSET?":
                    code = int("".join([f"{i}" for i in reversed(self.solenoid_state)]), 2)
                    result = f"{code}"
                elif atoms[0] == "MFC?":
                    if self.opstate in ["ident", "ident_2", "sampling", "clean", "reference"]:
                        self.mfc_value = random.randrange(10, 100)
                    else:
                        self.mfc_value = 0
                    result = f"{self.mfc_value}"
                elif atoms[0] == "OPSTATE":
                    new_state = atoms[1].lower()
                    if new_state in opstates:
                        if self.opstate != new_state:
                            self.opstate = new_state
                            self.opstate_changed.set()
                    else:
                        result = "-1"
                elif atoms[0] == "OPSTATE?":
                    result = f"{self.opstate}"
                elif atoms[0] == "SERNUM":
                    self.sernum = int(atoms[1])
                elif atoms[0] == "SLOTID":
                    self.bank = int(atoms[1])
                elif atoms[0] == "SLOTID?":
                    result = f"{self.bank}"
                else:
                    result = "-1"
        except:
            result = "-1"
        return result

    async def fsm(self):
        self.opstate_changed.set()
        while True:
            await self.opstate_changed.wait()
            self.opstate_changed.clear()
            # print(self.opstate)
            if self.opstate == "power_off":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 1
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0
                self.clean_solenoid_state = 0
            elif self.opstate == "power_up":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 1
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0
                self.clean_solenoid_state = 0
            elif self.opstate == "standby":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = self.BYPASS_ACTIVE
                self.clean_solenoid_state = 0
            elif self.opstate == "ident":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0.0
                self.clean_solenoid_state = 0
                start = time.time()
                while time.time() < start + 1.0:
                    if self.opstate != "ident":
                        break
                    await asyncio.sleep(0.1)
                else:
                    self.opstate = "ident_2"
                    self.opstate_changed.set()
            elif self.opstate == "ident_2":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 1
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0.0
                start = time.time()
                while time.time() < start + 1.0:
                    if self.opstate != "ident_2":
                        break
                    await asyncio.sleep(0.1)
                else:
                    self.opstate = "standby"
                    for i, _ in enumerate(self.active_chan):
                        self.active_chan[i] = 1 if random.uniform(0.0, 1.0) > 0.5 else 0
                    # print(self.active_chan)
                    self.opstate_changed.set()
            elif self.opstate == "clean":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = self.BYPASS_ACTIVE
                self.clean_solenoid_state = 1
            elif self.opstate == "reference":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 0
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = self.BYPASS_ACTIVE
                self.clean_solenoid_state = 1
            elif self.opstate == "fault":
                for i, _ in enumerate(self.solenoid_state):
                    self.solenoid_state[i] = 1
                for i, _ in enumerate(self.bypass_values):
                    self.bypass_values[i] = 0
                self.clean_solenoid_state = 0
