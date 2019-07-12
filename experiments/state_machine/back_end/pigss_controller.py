#!/usr/bin/env python3

import asyncio
import json
from enum import Enum

from async_hsm import Ahsm, Event, Framework, run_forever, Signal, Spy, TimeEvent, state
from pigss_payloads import PcResponsePayload, PcSendPayload

from piglet_manager import PigletManager

class UiStatus(str, Enum):
    DISABLED = "DISABLED"
    READY = "READY"
    ACTIVE = "ACTIVE"
    CLEAN = "CLEAN"
    REFERENCE = "REFERENCE"


def setbits(mask):
    """Return the bits set in the integer `mask` """
    result = []
    bit = 0
    while mask > 0:
        if mask % 2:
            result.append(bit)
        mask >>= 1
        bit += 1
    return result


class PigssController(Ahsm):
    num_banks = 4
    num_chans_per_bank = 8

    def __init__(self):
        super().__init__()
        self.status = {}
        self.send_queue = None
        self.receive_queue = None
        self.piglet_manager = None

    def set_queues(self, send_queue, receive_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue

    def set_piglet_manager(self, piglet_manager):
        self.piglet_manager = piglet_manager

    async def process_receive_queue_task(self):
        event_by_element = dict(
            standby=Signal.BTN_STANDBY,
            identify=Signal.BTN_IDENTIFY,
            reference=Signal.BTN_REFERENCE,
            clean=Signal.BTN_CLEAN,
            run=Signal.BTN_RUN,
            channel=Signal.BTN_CHANNEL,
        )
        while True:
            try:
                msg = json.loads(await self.receive_queue.get())
                print(f"Received from socket {msg}")
                Framework.publish(Event(event_by_element[msg["element"]], msg))
            except KeyError:
                print("Cannot find event associated with socket message - ignoring")

    def get_status(self):
        return self.status

    def set_status(self, path, value):
        """Set the status of the element specified by `path` to the given `value`.
        The status is kept in the nested dictionary `self.status`, and `path` is a
        list of strings which navigate through the levels of the dictionary. Thus
        for example, ["identify"] is the path to the Identify button, the path to 
        the Chan 3 button in bank 2 is ["channel", 2, 3] and ["clean",3] is the 
        path to the Clean button in bank 3.
        We construct a shadow object which is the portion of self.status that has
        to be updated. This is sent to the front end via a web socket in order to 
        allow the UI to be updated.
        """
        d = self.status
        shadow = {}
        o = shadow
        for p in path[:-1]:
            o[p] = {}
            if p not in d:
                d[p] = {}
            d = d[p]
            o = o[p]
        d[path[-1]] = value
        o[path[-1]] = value
        print(f"Setting status of {path} to {value}")
        asyncio.ensure_future(self.send_queue.put(json.dumps(shadow)))

    @state
    def _initial(self, e):
        self.bank = None
        self.bank_to_update = None
        self.channel = None
        # Keyed by bank. Its values are the masks corresponding to active channels
        # e.g. {1: 0, 2:64, 3:0, 4:0} represents channel active 7 in bank 2
        self.chan_active = {1: 0, 2: 0, 3: 0, 4: 0}
        Signal.register("PC_ABORT")
        Signal.register("PC_SEND")
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("PC_ERROR", self)
        Framework.subscribe("PC_TIMEOUT", self)
        Framework.subscribe("PC_RESPONSE", self)
        Framework.subscribe("BTN_STANDBY", self)
        Framework.subscribe("BTN_IDENTIFY", self)
        Framework.subscribe("BTN_PLAN", self)
        Framework.subscribe("BTN_RUN", self)
        Framework.subscribe("BTN_REFERENCE", self)
        Framework.subscribe("BTN_CLEAN", self)
        Framework.subscribe("BTN_CHANNEL", self)
        Framework.subscribe("TERMINATE", self)
        self.te = TimeEvent("UI_TIMEOUT")
        return self.tran(self._operational)

    @state
    def _operational(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["standby"], UiStatus.READY)
            self.set_status(["identify"], UiStatus.READY)
            self.set_status(["run"], UiStatus.DISABLED)
            self.set_status(["plan"], UiStatus.DISABLED)
            self.set_status(["reference"], UiStatus.READY)
            for i in range(self.num_banks):
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", i+1], UiStatus.READY)
                self.set_status(["bank", i+1], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    self.set_status(["channel", i+1, j+1], UiStatus.DISABLED)
            return self.handled(e)
        elif sig == Signal.TERMINATE:
            Framework.stop()
            return self.handled(e)
        elif sig == Signal.BTN_STANDBY:
            return self.tran(self._standby)
        elif sig == Signal.BTN_IDENTIFY:
            return self.tran(self._identify)
        elif sig == Signal.BTN_RUN:
            if self.status["run"] != UiStatus.DISABLED:
                return self.tran(self._run)
        elif sig == Signal.BTN_PLAN:
            if self.status["plan"] != UiStatus.DISABLED:
                return self.tran(self._plan)
        elif sig == Signal.BTN_REFERENCE:
            if self.status["reference"] != UiStatus.DISABLED:
                return self.tran(self._reference)
        elif sig == Signal.BTN_CLEAN:
            if self.status["clean"][e.value["bank"]] != UiStatus.DISABLED:
                self.bank = e.value["bank"]
                return self.tran(self._clean)
        return self.super(self.top)

    @state
    def _standby(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._standby1)
        elif sig == Signal.EXIT:
            self.set_status(["standby"], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.BTN_STANDBY:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _standby1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_all_piglets("OPSTATE standby"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._standby2)
        return self.super(self._standby)

    @state
    def _standby2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["standby"], UiStatus.ACTIVE)
            return self.handled(e)
        return self.super(self._standby)


    @state
    def _reference(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._reference1)
        elif sig == Signal.EXIT:
            self.set_status(["reference"], UiStatus.READY)
            for i in range(self.num_banks):
                # Use 1-origin for numbering banks and channels
                self.set_status(["bank", i+1], UiStatus.READY)

            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.BTN_REFERENCE:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _reference1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_all_piglets("OPSTATE reference"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._reference2)
        return self.super(self._reference)

    @state
    def _reference2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["reference"], UiStatus.ACTIVE)
            for i in range(self.num_banks):
                # Use 1-origin for numbering banks and channels
                self.set_status(["bank", i+1], UiStatus.REFERENCE)

            return self.handled(e)
        return self.super(self._reference)

    @state
    def _clean(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._clean1)
        elif sig == Signal.EXIT:
            for i in range(self.num_banks):
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", i+1], UiStatus.READY)
                self.set_status(["bank", i+1], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    if self.get_status()["channel"][i+1][j+1] == UiStatus.CLEAN:
                        self.set_status(["channel", i+1, j+1], UiStatus.READY)

            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.BTN_CLEAN:  # and self.get_status()["clean"][e.value["bank"]] == UiStatus.CLEAN:
            self.bank = e.value["bank"]
            if self.get_status()["clean"][self.bank] == UiStatus.CLEAN:
                return self.handled(e)
            else:
                return self.tran(self._clean1)
        return self.super(self._operational)

    @state
    def _clean1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_one_piglet(self.bank, "OPSTATE clean"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._clean2)
        return self.super(self._clean)

    @state
    def _clean2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            # Use 1-origin for numbering banks and channels
            self.set_status(["clean", self.bank], UiStatus.CLEAN)
            self.set_status(["bank", self.bank], UiStatus.CLEAN)
            for j in range(self.num_chans_per_bank):
                if self.get_status()["channel"][self.bank][j+1] == UiStatus.READY:
                    self.set_status(["channel", self.bank, j+1], UiStatus.CLEAN)

            return self.handled(e)
        return self.super(self._clean)

    @state
    def _identify(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._identify1)
        elif sig == Signal.ENTRY:
            self.set_status(["identify"], UiStatus.ACTIVE)
            self.bank = 1
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["identify"], UiStatus.READY)
            for i in range(self.num_banks):
                # Use 1-origin for numbering banks and channels
                self.set_status(["bank", i+1], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.BTN_IDENTIFY:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _identify1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_one_piglet(self.bank, "OPSTATE ident"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._identify2)
        return self.super(self._identify)

    @state
    def _identify2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["bank", self.bank], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS:
            print(e.value)
            msg = json.loads(e.value)
            print(f"In identify2: {msg['status'][self.bank-1]['STATE']}")
            if msg['status'][self.bank-1]['STATE'].startswith('ident'):
                return self.tran(self._identify3)
        return self.super(self._identify)

    @state
    def _identify3(self, e):
        sig = e.signal
        if sig == Signal.PIGLET_STATUS:
            msg = json.loads(e.value)
            print(f"In identify3: {msg['status'][self.bank-1]['STATE']}")
            if msg['status'][self.bank-1]['STATE'] == 'standby':
                return self.tran(self._identify4)
        return self.super(self._identify)

    @state
    def _identify4(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_one_piglet(self.bank, "CHANAVAIL?"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            msg = int(e.value)  # Integer representing available channels
            active = [1 if int(c) else 0 for c in reversed(format(msg, '08b'))]
            # Update the states of the channel buttons in the bank
            for i, stat in enumerate(active):
                self.set_status(["channel", self.bank, i+1], UiStatus.READY if stat else UiStatus.DISABLED)
            self.set_status(["bank", self.bank], UiStatus.READY)
            # Go to the next bank, and continue identification if the bank is present
            self.bank += 1
            if self.bank <= self.num_banks:
                return self.tran(self._identify1)
            else:
                # Otherwise, enable run and plan buttons and go back to standby since identification is complete
                self.set_status(["run"], UiStatus.READY)
                self.set_status(["plan"], UiStatus.READY)
                return self.tran(self._standby1)
        return self.super(self._identify)

    @state
    def _run(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for i in range(self.num_banks):
                self.chan_active[i+1] = 0
            asyncio.create_task(self.piglet_manager.send_to_all_piglets("CHANSET 0"))
            return self.handled(e)
        elif sig == Signal.EXIT:
            for i in range(self.num_banks):
                mask = self.chan_active[i+1]
                # Turn off ACTIVE states in UI for active channels
                for j in setbits(mask):
                    self.set_status(["channel", i+1, j+1], UiStatus.READY)
                self.chan_active[i+1] = 0
            asyncio.create_task(self.piglet_manager.send_to_all_piglets("CHANSET 0"))
            self.set_status(["run"], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._run1)
        elif sig == Signal.BTN_RUN:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _run1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.piglet_manager.send_to_all_piglets("OPSTATE sampling"))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._run2)
        return self.super(self._run)

    @state
    def _run2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["run"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.BTN_CHANNEL:
            if self.status["channel"][e.value["bank"]][e.value["channel"]] == UiStatus.READY:
                self.bank_to_update = 1
                self.bank = e.value["bank"]
                self.channel = e.value["channel"]
                print(f"\nBTN_CHANNEL: {self.bank} {self.channel}")
                mask = 1 << (self.channel - 1)
                # For this version, we can only have one active channel, so
                #  replace the currently active channel with the selected one
                for i in range(self.num_banks):
                    bank = i + 1
                    # Turn off ACTIVE states in UI for active channels
                    for j in setbits(self.chan_active[bank]):
                        self.set_status(["channel", bank, j+1], UiStatus.READY)
                    # Replace with the selected channel
                    if bank == self.bank:
                        self.chan_active[bank] = mask
                    else:
                        self.chan_active[bank] = 0
                return self.tran(self._run21)
        return self.super(self._run)

    @state
    def _run21(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            mask = self.chan_active[self.bank_to_update]
            print(f"\nSending to piglet at {self.bank_to_update}, CHANSET {mask}")
            asyncio.create_task(self.piglet_manager.send_to_one_piglet(self.bank_to_update, f"CHANSET {mask}"))
            for j in setbits(mask):
                self.set_status(["channel", self.bank_to_update, j+1], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            self.bank_to_update += 1
            if self.bank_to_update <= self.num_banks:
                return self.tran(self._run21)
            else:     
                return self.tran(self._run2)
        return self.super(self._run2)


if __name__ == "__main__":
    # Uncomment this line to get a visual execution trace (to demonstrate debugging)
    from async_hsm.SimpleSpy import SimpleSpy
    Spy.enable_spy(SimpleSpy)

    pc = PigssController()
    pc.start(1)

    event = Event(Signal.BTN_STANDBY, None)
    Framework.publish(event)
    event = Event(Signal.TERMINATE, None)
    Framework.publish(event)

    run_forever()
