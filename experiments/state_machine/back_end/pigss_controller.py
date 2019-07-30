#!/usr/bin/env python3

import asyncio
import collections
import glob
import html
import json
import ntpath
import os
import re
import time
import traceback
from enum import Enum, IntEnum

from async_hsm import (Ahsm, Event, Framework, Signal, Spy, TimeEvent,
                       run_forever, state)
from pigss_payloads import (PcResponsePayload, PcSendPayload,
                            PigletRequestPayload, PlanError)

PLAN_FILE_DIR = "/temp/plan_files"


class UiStatus(str, Enum):
    DISABLED = "DISABLED"
    READY = "READY"
    AVAILABLE = "AVAILABLE"
    ACTIVE = "ACTIVE"
    CLEAN = "CLEAN"
    REFERENCE = "REFERENCE"


class PlanPanelType(IntEnum):
    NONE = 0
    PLAN = 1
    LOAD = 2
    SAVE = 3


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
    num_chans_per_bank = 8

    def __init__(self, all_banks):
        super().__init__()
        self.error_list = collections.deque(maxlen=32)
        self.status = {}
        self.all_banks = all_banks
        self.plan = {
            "max_steps": 32,
            "panel_to_show": int(PlanPanelType.NONE),
            "current_step": 0,
            "looping": False,
            "focus": {
                "row": 1,
                "column": 1
            },
            "last_step": 0,
            "steps": {},
            "num_plan_files": 0,
            "plan_files": {},
            "plan_filename": "",
        }
        self.modal_info = {
            "show": False,
            "html": "<h2>Example Modal Dialog</h2><p>Test message</p>",
            "num_buttons": 2,
            "buttons": {
                1: {
                    "caption": "OK",
                    "className": "btn btn-success btn-large",
                    "response": "modal_ok"
                },
                2: {
                    "caption": "Cancel",
                    "className": "btn btn-danger btn-large",
                    "response": "modal_close"
                }
            }
        }
        self.send_queue = None
        self.receive_queue = None

    def set_queues(self, send_queue, receive_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue

    def get_plan_filenames(self):
        # Get list of plan filenames and update the entry in self.plan. This also
        #  informs any clients connected via a web socket of the list
        filenames = sorted(glob.glob(os.path.join(PLAN_FILE_DIR, "*.pln")))
        self.set_plan(["plan_files"], {i + 1: os.path.splitext(ntpath.basename(name))[0] for i, name in enumerate(filenames)})
        self.set_plan(["num_plan_files"], len(filenames))
        return filenames

    async def process_receive_queue_task(self):
        event_by_element = dict(
            standby=Signal.BTN_STANDBY,
            identify=Signal.BTN_IDENTIFY,
            reference=Signal.BTN_REFERENCE,
            modal_close=Signal.MODAL_CLOSE,
            modal_ok=Signal.MODAL_OK,
            plan=Signal.BTN_PLAN,
            plan_cancel=Signal.BTN_PLAN_CANCEL,
            plan_delete=Signal.BTN_PLAN_DELETE,
            plan_insert=Signal.BTN_PLAN_INSERT,
            plan_load=Signal.BTN_PLAN_LOAD,
            plan_load_cancel=Signal.BTN_PLAN_LOAD_CANCEL,
            plan_load_filename=Signal.PLAN_LOAD_FILENAME,
            plan_loop=Signal.BTN_PLAN_LOOP,
            plan_ok=Signal.BTN_PLAN_OK,
            plan_panel=Signal.PLAN_PANEL_UPDATE,
            plan_save=Signal.BTN_PLAN_SAVE,
            plan_save_cancel=Signal.BTN_PLAN_SAVE_CANCEL,
            plan_save_filename=Signal.PLAN_SAVE_FILENAME,
            plan_delete_filename=Signal.BTN_PLAN_DELETE_FILENAME,
            plan_save_ok=Signal.BTN_PLAN_SAVE_OK,
            clean=Signal.BTN_CLEAN,
            run=Signal.BTN_RUN,
            channel=Signal.BTN_CHANNEL,
        )
        while True:
            try:
                msg = json.loads(await self.receive_queue.get())
                # print(f"Received from socket {msg}")
                Framework.publish(Event(event_by_element[msg["element"]], msg))
            except KeyError:
                print("Cannot find event associated with socket message - ignoring")

    def get_modal_info(self):
        return self.modal_info

    def get_status(self):
        return self.status

    def get_plan(self):
        return self.plan

    def modify_value_in_nested_dict(self, target, path, value=None):
        """Modify a portion of the "target" which is a nested dictionary. The
        specified "path" is a list of strings which navigate through the levels
        of the dictionary. For example, if "target" is the dictionary
        {
            "identify": READY,
            "clean": {1: DISABLED, 2: READY},
            "channel": {
                1: {1: READY, 2: READY},
                2: {1: ACTIVE, 2: DISABLED}
            }
        }
        we may specify paths such as ["identify"], ["clean", 2], ["channel", 2, 1]
        and ["channel", 1] to refer to specific elements of the target that we wish
        to replace by "value".

        If the path does not yet exist in the target, it is created and set to the
        specified value.

        The function modifies the target in place and returns a "shadow" dictionary
        containing the portion of the target that was modified. For example with the
        above target, path=["channel", 1] and value={4: DISABLED, 5:ACTIVE} the returned
        dictionary is {"channel": {1: {4: DISABLED, 5: ACTIVE}}}.
        """
        if path:
            d = target
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
            return shadow
        else:
            target.clear()
            target.update(value)
            return value

    def set_modal_info(self, path, value):
        """Set the portion of self.modal_info specified by `path` to the given `value`.
        A shadow dictionary containing the change is sent via a websocket to inform the UI
        of the change in the plan.
        """
        shadow = self.modify_value_in_nested_dict(self.modal_info, path, value)
        # print(f"Setting plan {path} to {value}, shadow is {shadow}")
        asyncio.ensure_future(self.send_queue.put(json.dumps({"modal_info": shadow})))

    def set_plan(self, path, value):
        """Set the portion of self.plan specified by `path` to the given `value`.
        A shadow dictionary containing the change is sent via a websocket to inform the UI
        of the change in the plan.
        """
        shadow = self.modify_value_in_nested_dict(self.plan, path, value)
        # print(f"Setting plan {path} to {value}, shadow is {shadow}")
        asyncio.ensure_future(self.send_queue.put(json.dumps({"plan": shadow})))

    def set_status(self, path, value):
        """Set the status of the element specified by `path` to the given `value`.
        The self.status attribute is modified in place and a shadow dictionary containing
        the change is sent via a websocket to inform the UI of the change of status.
        """
        shadow = self.modify_value_in_nested_dict(self.status, path, value)
        # print(f"Setting status of {path} to {value}, shadow is {shadow}")
        asyncio.ensure_future(self.send_queue.put(json.dumps({"uistatus": shadow})))

    def plan_panel_update(self, msg):
        """Handle change of focus and edits in the duration column of the plan panel"""
        if "focus" in msg:
            data = msg["focus"]
            row = data["row"]
            column = data["column"]
            if row <= self.plan["last_step"] or (row == self.plan["last_step"] + 1 and column == 1):
                self.set_plan(["focus"], {"row": row, "column": column})
            else:
                self.set_plan(["focus"], self.plan["focus"])
        elif "duration" in msg:
            row = msg["row"]
            if row <= self.plan["last_step"]:
                try:
                    duration = int(msg["duration"]) if msg["duration"] else 0
                    self.set_plan(["steps", row, "duration"], duration)
                except ValueError:
                    pass
        else:
            print(f"Unknown message {msg}")

    def add_channel_to_plan(self, msg):
        """Handle a channel button press, adding the bank and channel to the plan
        at the location of the focussed row"""
        bank = msg["bank"]
        channel = msg["channel"]
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        if column == 2:
            row += 1
        if row <= self.plan["last_step"]:
            duration = self.plan["steps"][row]["duration"]
        else:
            duration = 0
        self.set_plan(["steps", row], {"bank": bank, "channel": channel, "duration": duration})
        if self.plan["last_step"] < row:
            self.set_plan(["last_step"], row)
        self.set_plan(["focus"], {"row": row, "column": 2})

    def plan_row_delete(self, msg):
        """Delete a row from the plan at the focussed row, moving up the remaining entries"""
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        num_steps = self.plan["last_step"]
        if num_steps > 0 and row <= num_steps:
            for r in range(row, self.plan["last_step"]):
                s = self.plan["steps"][r + 1]
                self.set_plan(["steps", r], {"bank": s["bank"], "channel": s["channel"], "duration": s["duration"]})
            self.set_plan(["last_step"], num_steps - 1)
        self.set_plan(["focus"], {"row": row, "column": column})

    def plan_row_insert(self, msg):
        """Insert a row into the plan at the focussed row, moving down the remaining entries"""
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        num_steps = self.plan["last_step"]
        if num_steps < self.plan["max_steps"] and row <= num_steps:
            for r in range(self.plan["last_step"], row - 1, -1):
                s = self.plan["steps"][r]
                self.set_plan(["steps", r + 1], {"bank": s["bank"], "channel": s["channel"], "duration": s["duration"]})
            self.set_plan(["steps", row], {"bank": 0, "channel": 0, "duration": 0})
            self.set_plan(["last_step"], num_steps + 1)
        self.set_plan(["focus"], {"row": row, "column": column})

    def validate_plan(self, check_avail=True):
        """Check that there are no errors in the plan. If an error is present,
        return the row and column of the first error and a string describing
        the problem"""
        if self.plan["last_step"] <= 0:
            return PlanError(True, f"Plan is empty", 1, 1)
        for i in range(self.plan["last_step"]):
            row = i + 1
            s = self.plan["steps"][row]
            if not (s["bank"] in self.all_banks and 1 <= s["channel"] <= self.num_chans_per_bank):
                return PlanError(True, f"Invalid port at step {row}", row, 1)
            elif not (s["duration"] > 0):
                return PlanError(True, f"Invalid duration at step {row}", row, 2)
            elif check_avail and not (self.status["channel"][s["bank"]][s["channel"]] in [UiStatus.READY]):
                return PlanError(True, f"Unavailable port at step {row}", row, 1)
        return PlanError(False)

    def save_plan_to_file(self):
        fname = os.path.join(PLAN_FILE_DIR, self.plan["plan_filename"] + ".pln")
        plan = {}
        for i in range(self.plan["last_step"]):
            row = i + 1
            s = self.plan["steps"][row]
            plan[str(row)] = {"active": {"bank": s["bank"], "channel": s["channel"]}, "duration": s["duration"]}
        with open(fname, "w") as fp:
            json.dump(plan, fp, indent=4)

    def load_plan_from_file(self):
        fname = os.path.join(PLAN_FILE_DIR, self.plan["plan_filename"] + ".pln")
        with open(fname, "r") as fp:
            plan = json.load(fp)
        assert isinstance(plan, dict), "Plan should be a dictionary"
        steps = {}
        last_step = len(plan)
        for i in range(last_step):
            row = i+1
            assert str(row) in plan, f"Plan is missing step {row}"
            step = plan[str(row)]
            assert "active" in step, f"Plan row {row} is missing 'active' key"
            assert "duration" in step, f"Plan row {row} is missing 'duration' key"
            steps[row] = {"bank": step["active"]["bank"], "channel": step["active"]["channel"], "duration": step["duration"]}
        self.set_plan(["steps"], steps)
        self.set_plan(["last_step"], last_step)
        self.set_plan(["focus"], {"row": last_step+1, "column": 1})

    def get_current_step_from_focus(self):
        step = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        if column == 2:
            step = step + 1
        if step > self.plan["last_step"]:
            step = step - self.plan["last_step"]
        return step

    def handle_error_signal(self, epoch_time, payload):
        self.error_list.append({"time": epoch_time, "payload": payload, "framework": Framework.get_info()})

    @state
    def _initial(self, e):
        self.bank = None
        self.bank_to_update = None
        self.banks_to_process = []
        self.channel = None
        self.plan_error = None
        self.plan_step_te = TimeEvent("PLAN_STEP_TIMER")
        self.plan_step_timer_target = 0
        self.filename_to_delete = ""
        self.state_after_delete = self._plan_load

        # Keyed by bank. Its values are the masks corresponding to active channels
        # e.g. {1: 0, 2:64, 3:0, 4:0} represents channel active 7 in bank 2
        self.chan_active = {1: 0, 2: 0, 3: 0, 4: 0}
        Signal.register("PC_ABORT")
        Signal.register("PC_SEND")
        Signal.register("PLAN_LOAD_SUCCESSFUL")
        Signal.register("PLAN_LOAD_FAILED")
        Signal.register("PLAN_SAVE_SUCCESSFUL")
        Signal.register("PLAN_SAVE_FAILED")
        Framework.subscribe("PIGLET_REQUEST", self)
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("PC_ERROR", self)
        Framework.subscribe("PC_TIMEOUT", self)
        Framework.subscribe("PC_RESPONSE", self)
        Framework.subscribe("BTN_STANDBY", self)
        Framework.subscribe("BTN_IDENTIFY", self)
        Framework.subscribe("BTN_PLAN", self)
        Framework.subscribe("BTN_PLAN_CANCEL", self)
        Framework.subscribe("BTN_PLAN_DELETE", self)
        Framework.subscribe("BTN_PLAN_DELETE_FILENAME", self)
        Framework.subscribe("BTN_PLAN_INSERT", self)
        Framework.subscribe("BTN_PLAN_LOAD", self)
        Framework.subscribe("BTN_PLAN_LOAD_CANCEL", self)
        Framework.subscribe("BTN_PLAN_LOOP", self)
        Framework.subscribe("BTN_PLAN_OK", self)
        Framework.subscribe("BTN_PLAN_SAVE", self)
        Framework.subscribe("BTN_PLAN_SAVE_CANCEL", self)
        Framework.subscribe("BTN_PLAN_SAVE_OK", self)
        Framework.subscribe("PLAN_LOAD_FILENAME", self)
        Framework.subscribe("PLAN_PANEL_UPDATE", self)
        Framework.subscribe("PLAN_SAVE_FILENAME", self)
        Framework.subscribe("BTN_RUN", self)
        Framework.subscribe("BTN_REFERENCE", self)
        Framework.subscribe("BTN_CLEAN", self)
        Framework.subscribe("BTN_CHANNEL", self)
        Framework.subscribe("MODAL_CLOSE", self)
        Framework.subscribe("MODAL_OK", self)
        Framework.subscribe("TERMINATE", self)
        Framework.subscribe("ERROR", self)
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
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", bank], UiStatus.READY)
                self.set_status(["bank", bank], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    self.set_status(["channel", bank, j + 1], UiStatus.DISABLED)
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._standby)
        elif sig == Signal.MODAL_CLOSE:
            self.set_modal_info(["show"], False)
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
        elif sig == Signal.ERROR:
            payload = e.value
            self.handle_error_signal(time.time(), payload)
            return self.handled(e)
        return self.super(self.top)

    @state
    def _standby(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            self.set_status(["standby"], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._standby1)
        elif sig == Signal.BTN_STANDBY:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _standby1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE standby", self.all_banks)))
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
        if sig == Signal.EXIT:
            self.set_status(["reference"], UiStatus.READY)
            for bank in self.all_banks:
                self.set_status(["bank", bank], UiStatus.READY)

            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._reference1)
        elif sig == Signal.BTN_REFERENCE:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _reference1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE reference", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._reference2)
        return self.super(self._reference)

    @state
    def _reference2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["reference"], UiStatus.ACTIVE)
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["bank", bank], UiStatus.REFERENCE)

            return self.handled(e)
        return self.super(self._reference)

    @state
    def _clean(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", bank], UiStatus.READY)
                self.set_status(["bank", bank], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    if self.get_status()["channel"][bank][j + 1] == UiStatus.CLEAN:
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)

            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._clean1)
        """
        elif sig == Signal.BTN_CLEAN:  # and self.get_status()["clean"][e.value["bank"]] == UiStatus.CLEAN:
            self.bank = e.value["bank"]
            if self.get_status()["clean"][self.bank] == UiStatus.CLEAN:
                return self.handled(e)
            else:
                return self.tran(self._clean1)
        """
        return self.super(self._operational)

    @state
    def _clean1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE clean", [self.bank])))
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
                if self.get_status()["channel"][self.bank][j + 1] == UiStatus.READY:
                    self.set_status(["channel", self.bank, j + 1], UiStatus.CLEAN)

            return self.handled(e)
        return self.super(self._clean)

    @state
    def _identify(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["identify"], UiStatus.ACTIVE)
            self.banks_to_process = self.all_banks.copy()
            self.bank = self.banks_to_process.pop(0)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["identify"], UiStatus.READY)
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["bank", bank], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._identify1)
        elif sig == Signal.BTN_IDENTIFY:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _identify1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE ident", [self.bank])))
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
            # print(f"In identify2: {msg['status'][self.bank-1]['STATE']}")
            if e.value[self.bank]['STATE'].startswith('ident'):
                return self.tran(self._identify3)
        return self.super(self._identify)

    @state
    def _identify3(self, e):
        sig = e.signal
        if sig == Signal.PIGLET_STATUS:
            # print(f"In identify3: {msg['status'][self.bank-1]['STATE']}")
            if e.value[self.bank]['STATE'] == 'standby':
                return self.tran(self._identify4)
        return self.super(self._identify)

    @state
    def _identify4(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("CHANAVAIL?", [self.bank])))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            msg = int(e.value[self.bank])  # Integer representing available channels
            active = [1 if int(c) else 0 for c in reversed(format(msg, '08b'))]
            # Update the states of the channel buttons in the bank
            for i, stat in enumerate(active):
                self.set_status(["channel", self.bank, i + 1], UiStatus.AVAILABLE if stat else UiStatus.DISABLED)
            self.set_status(["bank", self.bank], UiStatus.READY)
            # Go to the next bank, and continue identification if the bank is present
            if self.banks_to_process:
                self.bank = self.banks_to_process.pop(0)
                return self.tran(self._identify1)
            else:
                # Otherwise, enable run and plan buttons and go back to standby since identification is complete
                self.set_status(["run"], UiStatus.READY)
                self.set_status(["plan"], UiStatus.READY)
                return self.tran(self._operational)
        return self.super(self._identify)

    @state
    def _run(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            self.set_status(["run"], UiStatus.READY)
            Framework.publish(Event(Signal.PC_ABORT, None))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run1)
        elif sig == Signal.BTN_RUN:
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._operational)
        return self.super(self._operational)

    @state
    def _run1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for bank in self.all_banks:
                self.chan_active[bank] = 0
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.AVAILABLE:
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("CHANSET 0", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.EXIT:
            """
            for bank in self.all_banks:
                mask = self.chan_active[i]
                # Turn off ACTIVE states in UI for active channels
                for j in setbits(mask):
                    self.set_status(["channel", bank, j+1], UiStatus.AVAILABLE)
                self.chan_active[bank] = 0
            """
            for bank in self.all_banks:
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] in [UiStatus.READY, UiStatus.ACTIVE]:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE standby", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._run11)
        return self.super(self._run)

    @state
    def _run11(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE sampling", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._run12)
        return self.super(self._run1)

    @state
    def _run12(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["run"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.BTN_CHANNEL:
            if self.status["channel"][e.value["bank"]][e.value["channel"]] == UiStatus.READY:
                self.banks_to_process = self.all_banks.copy()
                self.bank_to_update = self.banks_to_process.pop(0)
                self.bank = e.value["bank"]
                self.channel = e.value["channel"]
                # print(f"\nBTN_CHANNEL: {self.bank} {self.channel}")
                mask = 1 << (self.channel - 1)
                # For this version, we can only have one active channel, so
                #  replace the currently active channel with the selected one
                for bank in self.all_banks:
                    # Turn off ACTIVE states in UI for active channels
                    for j in setbits(self.chan_active[bank]):
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
                    # Replace with the selected channel
                    if bank == self.bank:
                        self.chan_active[bank] = mask
                    else:
                        self.chan_active[bank] = 0
                return self.tran(self._run121)
        return self.super(self._run1)

    @state
    def _run121(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            mask = self.chan_active[self.bank_to_update]
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload(f"CHANSET {mask}", [self.bank_to_update])))
            for j in setbits(mask):
                self.set_status(["channel", self.bank_to_update, j + 1], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            if self.banks_to_process:
                self.bank_to_update = self.banks_to_process.pop(0)
                return self.tran(self._run121)
            else:
                return self.handled(e)
        return self.super(self._run12)

    @state
    def _plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for bank in self.all_banks:
                self.set_status(["clean", bank], UiStatus.DISABLED)
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.AVAILABLE:
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
            return self.handled(e)
        elif sig == Signal.EXIT:
            for bank in self.all_banks:
                self.set_status(["clean", bank], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.READY:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            self.set_plan(["panel_to_show"], int(PlanPanelType.NONE))
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._plan_plan)
        elif sig == Signal.BTN_PLAN:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _plan_delete_file(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            msg = f"Delete file {self.filename_to_delete}?"
            self.set_modal_info(
                [], {
                    "show": True,
                    "html": f"<h2>Confirm file deletion</h2><p>{msg}</p>",
                    "num_buttons": 2,
                    "buttons": {
                        1: {
                            "caption": "OK",
                            "className": "btn btn-success btn-large",
                            "response": "modal_ok"
                        },
                        2: {
                            "caption": "Cancel",
                            "className": "btn btn-danger btn-large",
                            "response": "modal_close"
                        }
                    }
                })
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_OK:
            fname = os.path.join(PLAN_FILE_DIR, self.filename_to_delete + ".pln")
            os.remove(fname)
            self.get_plan_filenames()
            return self.tran(self.state_after_delete)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self.state_after_delete)
        return self.super(self._plan)

    @state
    def _plan_plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_plan(["panel_to_show"], int(PlanPanelType.PLAN))
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_OK:
            self.plan_error = self.validate_plan(check_avail=True)
            if not self.plan_error.error:
                self.set_plan(["looping"], False)
                self.set_plan(["current_step"], self.get_current_step_from_focus())
                return self.tran(self._plan_plan2)
            else:
                return self.tran(self._plan_plan1)
        elif sig == Signal.BTN_PLAN_LOOP:
            self.plan_error = self.validate_plan(check_avail=True)
            if not self.plan_error.error:
                self.set_plan(["looping"], True)
                self.set_plan(["current_step"], self.get_current_step_from_focus())
                return self.tran(self._plan_plan2)
            else:
                return self.tran(self._plan_plan1)
        elif sig == Signal.BTN_PLAN_CANCEL:
            return self.tran(self._operational)
        elif sig == Signal.BTN_PLAN_DELETE:
            self.plan_row_delete(e.value)
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_INSERT:
            self.plan_row_insert(e.value)
            return self.handled(e)
        elif sig == Signal.PLAN_PANEL_UPDATE:
            self.plan_panel_update(e.value)
            return self.handled(e)
        elif sig == Signal.BTN_CHANNEL:
            self.add_channel_to_plan(e.value)
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_SAVE:
            self.plan_error = self.validate_plan(check_avail=False)
            if not self.plan_error.error:
                return self.tran(self._plan_save)
            else:
                return self.tran(self._plan_plan1)
        elif sig == Signal.BTN_PLAN_LOAD:
            return self.tran(self._plan_load)
        return self.super(self._plan)


    @state
    def _plan_file(self, e):
        sig = e.signal
        if sig == Signal.BTN_PLAN_DELETE_FILENAME:
            self.filename_to_delete = e.value["name"]
            return self.tran(self._plan_delete_file)
        return self.super(self._plan)

    @state
    def _plan_load(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_plan(["panel_to_show"], int(PlanPanelType.LOAD))
            self.state_after_delete = self._plan_load
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_LOAD_CANCEL:
            return self.tran(self._plan)
        elif sig == Signal.PLAN_LOAD_FILENAME:
            self.set_plan(["plan_filename"], e.value["name"])
            return self.tran(self._plan_load1)
        return self.super(self._plan_file)

    @state
    def _plan_load1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            try:
                self.load_plan_from_file()
                self.postFIFO(Event(Signal.PLAN_LOAD_SUCCESSFUL, None))
            except:
                self.postFIFO(Event(Signal.PLAN_LOAD_FAILED, traceback.format_exc()))
            return self.handled(e)
        elif sig == Signal.PLAN_LOAD_SUCCESSFUL:
            return self.tran(self._plan)
        elif sig == Signal.PLAN_LOAD_FAILED:
            self.plan_error = PlanError(True, f'<pre>{html.escape(e.value)}</pre>')
            return self.tran(self._plan_load11)
        return self.super(self._plan_load)

    @state
    def _plan_load11(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_modal_info([], {"show": True, "html": f"<h3>Plan load error</h3><p>{self.plan_error.message}</p>", "num_buttons": 0})
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan_load)
        return self.super(self._plan_load1)

    @state
    def _plan_save(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_plan(["panel_to_show"], int(PlanPanelType.SAVE))
            self.state_after_delete = self._plan_save
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_SAVE_CANCEL:
            return self.tran(self._plan)
        elif sig == Signal.PLAN_SAVE_FILENAME:
            # Remove non alphanumeric characters
            self.set_plan(["plan_filename"], re.sub(r"\W", "", e.value["name"]))
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_SAVE_OK:
            fname = os.path.join(PLAN_FILE_DIR, self.plan["plan_filename"] + ".pln")
            if os.path.isfile(fname):
                return self.tran(self._plan_save1)
            else:
                return self.tran(self._plan_save2)
        return self.super(self._plan_file)

    @state
    def _plan_save1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            msg = "File exists. Overwrite?"
            self.set_modal_info(
                [], {
                    "show": True,
                    "html": f"<h2>Confirm file overwrite</h2><p>{msg}</p>",
                    "num_buttons": 2,
                    "buttons": {
                        1: {
                            "caption": "OK",
                            "className": "btn btn-success btn-large",
                            "response": "modal_ok"
                        },
                        2: {
                            "caption": "Cancel",
                            "className": "btn btn-danger btn-large",
                            "response": "modal_close"
                        }
                    }
                })
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_OK:
            return self.tran(self._plan_save2)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan_save)
        return self.super(self._plan_save)

    @state
    def _plan_save2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            try:
                self.save_plan_to_file()
                self.postFIFO(Event(Signal.PLAN_SAVE_SUCCESSFUL, None))
            except:
                self.postFIFO(Event(Signal.PLAN_SAVE_FAILED, traceback.format_exc()))
            return self.handled(e)
        elif sig == Signal.PLAN_SAVE_SUCCESSFUL:
            self.get_plan_filenames()
            return self.tran(self._plan)
        elif sig == Signal.PLAN_SAVE_FAILED:
            self.plan_error = PlanError(True, f'<pre>{html.escape(e.value)}</pre>')
            return self.tran(self._plan_save21)
        return self.super(self._plan_save)

    @state
    def _plan_save21(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_modal_info([], {"show": True, "html": f"<h3>Plan save error</h3><p>{self.plan_error.message}</p>", "num_buttons": 0})
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan_save)
        return self.super(self._plan_save2)

    @state
    def _plan_plan1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_modal_info([], {
                "show": True,
                "html": f"<h3>Plan error</h3><p>{self.plan_error.message}</p>",
                "num_buttons": 0
            })
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            self.set_plan(["focus"], {"row": self.plan_error.row, "column": self.plan_error.column})
            return self.handled(e)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan)
        return self.super(self._plan_plan)

    @state
    def _plan_plan2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            msg = "Loop" if self.plan['looping'] else "Run"
            msg += f" plan starting at step {self.plan['current_step']}"
            self.set_modal_info(
                [], {
                    "show": True,
                    "html": f"<h2>Confirm Plan</h2><p>{msg}</p>",
                    "num_buttons": 2,
                    "buttons": {
                        1: {
                            "caption": "OK",
                            "className": "btn btn-success btn-large",
                            "response": "modal_ok"
                        },
                        2: {
                            "caption": "Cancel",
                            "className": "btn btn-danger btn-large",
                            "response": "modal_close"
                        }
                    }
                })
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_OK:
            return self.tran(self._run_plan)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan)
        return self.super(self._plan_plan)

    @state
    def _run_plan(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            self.set_status(["run"], UiStatus.READY)
            self.set_status(["plan"], UiStatus.READY)
        elif sig == Signal.INIT:
            return self.tran(self._run_plan1)
        elif sig == Signal.BTN_RUN:
            return self.handled(e)
        elif sig == Signal.BTN_PLAN:
            return self.handled(e)
        if sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._operational)
        return self.super(self._operational)

    @state
    def _run_plan1(self, e):
        sig = e.signal
        if sig == Signal.PIGLET_RESPONSE:
            return self.tran(self._run_plan11)
        elif sig == Signal.ENTRY:
            for bank in self.all_banks:
                self.chan_active[bank] = 0
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("CHANSET 0", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.EXIT:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE standby", self.all_banks)))
            return self.handled(e)
        return self.super(self._run_plan)

    @state
    def _run_plan11(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE sampling", self.all_banks)))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            self.plan_step_timer_target = asyncio.get_event_loop().time()
            return self.tran(self._run_plan12)
        return self.super(self._run_plan1)

    @state
    def _run_plan12(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["run"], UiStatus.ACTIVE)
            self.set_status(["plan"], UiStatus.ACTIVE)
            current_step = self.plan["current_step"]
            self.plan_step_timer_target += self.plan["steps"][current_step]["duration"]
            self.plan_step_te.postAt(self, self.plan_step_timer_target)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.plan_step_te.disarm()
            for bank in self.all_banks:
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.ACTIVE:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run_plan121)
        elif sig == Signal.PLAN_STEP_TIMER:
            current_step = self.plan["current_step"]
            last_step = self.plan["last_step"]
            looping = self.plan["looping"]
            if current_step >= last_step and not looping:
                # All steps done
                return self.tran(self._operational)
            else:
                # Set up for next step
                current_step += 1
                if current_step > last_step:
                    current_step -= last_step
                self.set_plan(["current_step"], current_step)
                return self.tran(self._run_plan12)
        return self.super(self._run_plan1)

    @state
    def _run_plan121(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.banks_to_process = self.all_banks.copy()
            self.bank_to_update = self.banks_to_process.pop(0)
            current_step = self.plan["current_step"]
            self.bank = self.plan["steps"][current_step]["bank"]
            self.channel = self.plan["steps"][current_step]["channel"]
            mask = 1 << (self.channel - 1)
            # For this version, we can only have one active channel, so
            #  replace the currently active channel with the selected one
            for bank in self.all_banks:
                # Turn off ACTIVE states in UI for active channels
                for j in setbits(self.chan_active[bank]):
                    self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
                # Replace with the selected channel
                if bank == self.bank:
                    self.chan_active[bank] = mask
                else:
                    self.chan_active[bank] = 0
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run_plan1211)
        elif sig == Signal.PIGLET_STATUS:
            for bank in self.all_banks:
                mask = e.value[bank]['SOLENOID_VALVES']
                sel = setbits(mask)
                for j in range(self.num_chans_per_bank):
                    current = self.status["channel"][bank][j + 1]
                    if current != UiStatus.DISABLED:
                        if j in sel:
                            if current != UiStatus.ACTIVE:
                                self.set_status(["channel", bank, j + 1], UiStatus.ACTIVE)
                        else:
                            if current != UiStatus.AVAILABLE:
                                self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            return self.handled(e)
        return self.super(self._run_plan12)

    @state
    def _run_plan1211(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            mask = self.chan_active[self.bank_to_update]
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload(f"CHANSET {mask}", [self.bank_to_update])))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            if self.banks_to_process:
                self.bank_to_update = self.banks_to_process.pop(0)
                return self.tran(self._run_plan1211)
            else:
                return self.handled(e)
        return self.super(self._run_plan121)


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
