#!/usr/bin/env python3
"""
Hierarchical state machine which controls the valves and flow in the
 piglets and the sampling rack. It also maintains the state of the system
 which can be displayed and controlled via a web-based UI that communicates
 using API calls and a web socket.
"""
import aiohttp
import asyncio
import collections
import glob
import html
import json
import os
import re
import requests
import time
from traceback import format_exc
from enum import Enum, IntEnum

import ntpath

from async_hsm import Ahsm, Event, Framework, Signal, TimeEvent, state
from back_end.database_access.aio_influx_database import AioInfluxDBWriter
from back_end.lologger.lologger_client import LOLoggerClient
from back_end.state_machines.pigss_payloads import (PigletRequestPayload,
                                                    PlanError,
                                                    ValveTransitionPayload)


log = LOLoggerClient(client_name="AppController", verbose=True)

PLAN_FILE_DIR = os.path.join(os.getenv("HOME"), ".config", "pigss", "plan_files")
if not os.path.isdir(PLAN_FILE_DIR):
    os.makedirs(PLAN_FILE_DIR, 0o755)


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
    EDIT = 4


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

    def __init__(self, farm=None):
        super().__init__()
        self.farm = farm
        self.error_list = collections.deque(maxlen=32)
        self.status = {}
        self.all_banks = []
        self.plan_name = ""
        self.last_running = ""
        self.last_running_details = {}
        self.plan = {
            "max_steps": 32,
            "current_step": 1,
            "focus": {
                "row": 1,
                "column": 1
            },
            "last_step": 0,
            "steps": {},
            "num_plan_files": 0,
            "plan_files": {},
            "plan_filename": "",
            "bank_names": {
                "1": {
                    "name": "Bank 1",
                    "channels": {
                        "1": "Ch. 1",
                        "2": "Ch. 2",
                        "3": "Ch. 3",
                        "4": "Ch. 4",
                        "5": "Ch. 5",
                        "6": "Ch. 6",
                        "7": "Ch. 7",
                        "8": "Ch. 8"
                    }
                },
                "2": {
                    "name": "Bank 2",
                    "channels": {
                        "1": "Ch. 1",
                        "2": "Ch. 2",
                        "3": "Ch. 3",
                        "4": "Ch. 4",
                        "5": "Ch. 5",
                        "6": "Ch. 6",
                        "7": "Ch. 7",
                        "8": "Ch. 8"
                    }
                },
                "3": {
                    "name": "Bank 3",
                    "channels": {
                        "1": "Ch. 1",
                        "2": "Ch. 2",
                        "3": "Ch. 3",
                        "4": "Ch. 4",
                        "5": "Ch. 5",
                        "6": "Ch. 6",
                        "7": "Ch. 7",
                        "8": "Ch. 8"
                    }
                },
                "4": {
                    "name": "Bank 4",
                    "channels": {
                        "1": "Ch. 1",
                        "2": "Ch. 2",
                        "3": "Ch. 3",
                        "4": "Ch. 4",
                        "5": "Ch. 5",
                        "6": "Ch. 6",
                        "7": "Ch. 7",
                        "8": "Ch. 8"
                    }
                }
            }
        }
        self.available_ports = {
            "available_ports": {
                "1": 0,
                "2": 0, 
                "3": 0,
                "4": 0
            }
        }
        self.modal_info = {
            "show": False,
            "html": "<h2 class='test'>Example Modal Dialog</h2><p>Test message</p>",
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
        self.timer = False
        self.send_queue = None
        self.receive_queue = None
        db_config = self.farm.config.get_time_series_database()
        self.db_writer = AioInfluxDBWriter(address=db_config["server"], db_port=db_config["port"], db_name=db_config["name"])

    def set_queues(self, send_queue, receive_queue):
        self.send_queue = send_queue
        self.receive_queue = receive_queue

    def get_available_ports(self):
        print("Getting available Ports ")
        return self.available_ports["available_ports"]

    async def fetch(self, session, url):
        async with session.get(url) as response:
            return await response.text()

    async def post_data(self, session, url, information=None):
        async with session.post(url, data=information) as res:
            return await res.text()

    async def put_data(self, session, url, information=None):
        async with session.put(url, data=information) as res:
            return await res.text()

    def get_bank_names(self):
        return self.plan["bank_names"]

    # async def get_plan_filenames(self):
    #     #TODO: Change to load from PlanService
    #     # Get list of plan filenames and update the entry in self.plan. This also
    #     #  informs any clients connected via a web socket of the list
    #     # filenames = sorted(glob.glob(os.path.join(PLAN_FILE_DIR, "*.pln")))
    #     # self.set_plan(["plan_files"], {i + 1: os.path.splitext(ntpath.basename(name))[0] for i, name in enumerate(filenames)})
    #     # self.set_plan(["num_plan_files"], len(filenames))
    #     await self.get_available_plans()
        

    # async def get_plan_names(self):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get("http://localhost:8000/manage_plan/api/v0.1/plan?names=true") as resp:
    #             print(await resp.json())

    async def save_port_history(self):
        print("Saving Port History ")
        data = [{
            "measurement": "port_history",
            "tags": {},
            "fields": {
                "available_ports": json.dumps(self.get_available_ports()),
                "bank_names": json.dumps(self.get_bank_names())
            },
            "time": time.time_ns()
        }]
        await asyncio.shield(self.db_writer.write_data(data))

    async def process_receive_queue_task(self):
        event_by_element = dict(standby=Signal.BTN_STANDBY,
                                identify=Signal.BTN_IDENTIFY,
                                reference=Signal.BTN_REFERENCE,
                                modal_close=Signal.MODAL_CLOSE,
                                modal_ok=Signal.MODAL_OK,
                                modal_step_1=Signal.MODAL_STEP_1,
                                plan=Signal.BTN_PLAN,
                                plan_cancel=Signal.BTN_PLAN_CANCEL,
                                plan_clear=Signal.BTN_PLAN_CLEAR,
                                plan_delete=Signal.BTN_PLAN_DELETE,
                                plan_insert=Signal.BTN_PLAN_INSERT,
                                plan_load=Signal.BTN_PLAN_LOAD,
                                plan_load_cancel=Signal.BTN_PLAN_LOAD_CANCEL,
                                plan_load_filename=Signal.PLAN_LOAD_FILENAME,
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
                                edit=Signal.BTN_EDIT,
                                edit_panel=Signal.CHANGE_NAME_BANK,
                                edit_cancel=Signal.EDIT_CANCEL,
                                edit_save=Signal.EDIT_SAVE,
                                plan_loop=Signal.BTN_PLAN_LOOP,
                                plan_run=Signal.BTN_PLAN_RUN,
                                load=Signal.BTN_LOAD,
                                load_cancel=Signal.BTN_LOAD_CANCEL,
                                load_filename=Signal.LOAD_FILENAME,
                                load_modal_ok=Signal.LOAD_MODAL_OK,
                                load_modal_cancel=Signal.LOAD_MODAL_CANCEL,
                                filename_ok=Signal.FILENAME_OK,
                                filename_cance=Signal.FILENAME_CANCEL
                                )
        while True:
            try:
                msg = json.loads(await self.receive_queue.get())
                Framework.publish(Event(event_by_element[msg["element"]], msg))
            except KeyError:
                log.warning(f"Cannot find event associated with socket message {msg['element']} - ignoring")

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
        try:
            self.send_queue.put_nowait(json.dumps({"modal_info": shadow}))
        except asyncio.queues.QueueFull:
            log.debug(f"Farm Send Queue Full\n{format_exc()}")
            log.error(f"Send Queue Full. Please report.")

    def set_plan(self, path, value):
        """Set the portion of self.plan specified by `path` to the given `value`.
        A shadow dictionary containing the change is sent via a websocket to inform the UI
        of the change in the plan.
        """
        shadow = self.modify_value_in_nested_dict(self.plan, path, value)
        try:
            self.send_queue.put_nowait(json.dumps({"plan": shadow}))
        except asyncio.queues.QueueFull:
            log.debug(f"Farm Send Queue Full\n{format_exc()}")
            log.error(f"Send Queue Full. Please report.")

    def set_available_ports(self, path, value):
        """Set the portion of self.plan specified by `path` to the given `value`.
        A shadow dictionary containing the change is sent via a websocket to inform the UI
        of the change in the plan.
        """
        shadow = self.modify_value_in_nested_dict(self.available_ports, path, value)
        try:
            self.send_queue.put_nowait(json.dumps({"available_ports": shadow}))
        except asyncio.queues.QueueFull:
            log.debug(f"Farm Send Queue Full\n{format_exc()}")
            log.error(f"Send Queue Full. Please report.")


    def set_status(self, path, value):
        """Set the status of the element specified by `path` to the given `value`.
        The self.status attribute is modified in place and a shadow dictionary containing
        the change is sent via a websocket to inform the UI of the change of status.
        """
        shadow = self.modify_value_in_nested_dict(self.status, path, value)
        try:
            self.send_queue.put_nowait(json.dumps({"uistatus": shadow}))
        except asyncio.queues.QueueFull:
            log.debug(f"Farm Send Queue Full\n{format_exc()}")
            log.error(f"Send Queue Full. Please report.")

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
                    # Do not throw eror while duration is edited. The back end is called on every
                    # keypress to maintain synchronization between clients.
                    pass
        elif "current_step" in msg:
            row = msg["current_step"]
            if row <= self.plan["max_steps"]:
                self.set_plan(["current_step"], row)

    async def timer_update(self):
        time_remaining = self.status["timer"]
        while time_remaining > 0 and self.timer:
            await asyncio.sleep(1)
            time_remaining -= 1
            self.set_status(["timer"], time_remaining)

    def add_to_plan(self, bank_config, reference):
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        if row >= self.plan["max_steps"] and column == 2:
            max_steps = self.plan["max_steps"]
            msg = f"Only {max_steps} steps are currently allowed"
            self.set_modal_info(
                [], {
                    "show": True,
                    "html": f"<h2 class='test'>Max Steps Reached</h2><p>{msg}</p>",
                    "num_buttons": 0,
                    "buttons": {}
                })
            return
        if column == 2:
            row += 1
        if row <= self.plan["last_step"]:
            duration = self.plan["steps"][row]["duration"]
        else:
            duration = 0
        self.set_plan(["steps", row], {"banks": bank_config, "reference": reference, "duration": duration})
        if self.plan["last_step"] < row:
            self.set_plan(["last_step"], row)
        self.set_plan(["focus"], {"row": row, "column": 2})

    def add_channel_to_plan(self, msg):
        """Handle a channel button press, adding the bank and channel to the plan
        at the location of the focussed row"""
        bank = msg["bank"]
        channel = msg["channel"]
        bank_config = {b: {"clean": 0, "chan_mask": 0} for b in self.all_banks}
        bank_config[bank]["chan_mask"] = 1 << (channel - 1)
        self.add_to_plan(bank_config, 0)

    def add_bank_to_clean_to_plan(self, bank):
        """Handle a clean button press in a bank. Add to plan at the location of the focussed row"""
        bank_config = {b: {"clean": 0, "chan_mask": 0} for b in self.all_banks}
        bank_config[bank]["clean"] = 1
        self.add_to_plan(bank_config, 0)

    def add_reference_to_plan(self):
        """Handle a reference button press in a bank. Add to plan at the location of the focussed row"""
        bank_config = {b: {"clean": 0, "chan_mask": 0} for b in self.all_banks}
        self.add_to_plan(bank_config, 1)

    def plan_clear(self):
        """Delete all rows of the plan"""
        self.set_plan(["last_step"], 0)
        self.set_plan(["steps"], {})
        self.set_plan(["current_step"], 1)
        self.set_plan(["focus"], {"row": 1, "column": 1})

    def plan_row_delete(self, msg):
        """Delete a row from the plan at the focussed row, moving up the remaining entries"""
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        num_steps = self.plan["last_step"]
        if num_steps > 0 and row <= num_steps:
            for r in range(row, self.plan["last_step"]):
                s = self.plan["steps"][r + 1]
                self.set_plan(["steps", r], s.copy())
            self.set_plan(["last_step"], num_steps - 1)
        if row == 1:
            column = 1
        else:
            row = row - 1
        self.set_plan(["focus"], {"row": row, "column": column})

    def plan_row_insert(self, msg):
        """Insert a row into the plan at the focussed row, moving down the remaining entries"""
        row = self.plan["focus"]["row"]
        column = self.plan["focus"]["column"]
        num_steps = self.plan["last_step"]
        if num_steps < self.plan["max_steps"] and row <= num_steps:
            for r in range(self.plan["last_step"], row - 1, -1):
                s = self.plan["steps"][r]
                self.set_plan(["steps", r + 1], s.copy())
            self.set_plan(["steps", row], {
                "banks": {b: {
                    "clean": 0,
                    "chan_mask": 0
                }
                          for b in self.all_banks},
                "reference": 0,
                "duration": 0
            })
            self.set_plan(["last_step"], num_steps + 1)
        self.set_plan(["focus"], {"row": row, "column": column})

    def validate_plan(self, check_avail=True, plan=None):
        """Check that there are no errors in the plan. If an error is present,
        return the row and column of the first error and a string describing
        the problem"""
        if plan == None:
            plan = self.plan
        if plan["last_step"] <= 0:
            return PlanError(True, f"Plan is empty", 1, 1)
        if not 1 <= plan["current_step"] <= plan["last_step"]:
            return PlanError(True, f"Pending step must be between 1 and {plan['last_step']}", 1, 1)
        min_plan_interval = self.farm.config.get_min_plan_interval()
        for i in range(plan["last_step"]):
            row = i + 1
            s = plan["steps"][row]
            if "duration" not in s or "reference" not in s or "banks" not in s:
                return PlanError(True, f"Malformed data at step {row}", row, 1)
            if not s["duration"] > 0 or s["duration"] < min_plan_interval:
                return PlanError(True, f"Invalid duration at step {row}. Duration must be greater than {min_plan_interval}.",
                                 row, 2)
            for bank in s["banks"]:
                if bank not in self.all_banks:
                    return PlanError(True, f"Invalid bank at step {row}", row, 1)
                bank_config = s["banks"][bank]
                if "chan_mask" not in bank_config or "clean" not in bank_config:
                    return PlanError(True, f"Invalid data for bank {bank} in step {row}", row, 1)
                if not 0 <= bank_config["chan_mask"] < 256:
                    return PlanError(True, f"Invalid channel selection for bank {bank} in step {row}", row, 1)
                if check_avail:
                    for j in setbits(bank_config["chan_mask"]):
                        if self.status["channel"][bank][j + 1] != UiStatus.READY:
                            return PlanError(True, f"Unavailable port at step {row}", row, 1)
        print("---> Plan Validated")
        return PlanError(False)

    def validate_plan_filename(self, filename, check_avail=True):
        if len(filename) == 0:
            return False
        return True

    def save_plan_to_file(self, filename):
        fname = os.path.join(PLAN_FILE_DIR, filename + ".pln")
        plan = {}
        for i in range(self.plan["last_step"]):
            row = i + 1
            s = self.plan["steps"][row]
            # Not strictly necessary to convert row to a string here, but is here to remind the
            # reader that serializing a dictionary via JSON turns all keys into strings
            plan[str(row)] = s
        try:
            with open(fname, "w") as fp:
                json.dump({"plan": plan, "bank_names": self.plan["bank_names"]}, fp, indent=4)
                log.debug(f"Plan file saved {fname}")
        except FileNotFoundError as fe:
            log.critical(f"Plan save error {fe}")
            raise

    async def save_plan_to_default(self):
        data = {
            "name": self.plan["plan_filename"],
            "details": self.plan,
            "user": 'admin',
            "is_running": 0,
            "is_deleted": 0
        }
        data_json = json.dumps(data)
        async with aiohttp.ClientSession() as session:
            res = await self.put_data(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan', data_json)
        await asyncio.sleep(1.0)

    async def get_available_plans(self):
        async with aiohttp.ClientSession() as session: 
            plans = await self.fetch(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan?names=true')
        await asyncio.sleep(1.0)
        plans = json.loads(plans)
        print("PLANS ++++++++++++++++++++++ ", plans)
        if plans["plans"]:
            num = len(plans["plans"])
            self.set_plan(["plan_files"], {i + 1: name for i, name in enumerate(plans["plans"])})
            self.set_plan(["num_plan_files"], num)
            print("PLAN FILES ", self.plan["plan_files"])

    async def get_last_running(self):
        async with aiohttp.ClientSession() as session: 
            last_run = await self.fetch(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan?last_running=true')
            running_plan = json.loads(last_run)
            if running_plan["name"]:
                print("PLAN DEETS =----> ", running_plan["details"])
                self.last_running = running_plan["name"]
                self.last_running_details = json.loads(running_plan["details"])
                self.plan = json.loads(running_plan["details"])
            ##create __default
            # data = {
            #     "name": "__default__",
            #     "details": self.last_running_details,
            #     "user": 'admin',
            #     "is_running": 0,
            #     "is_deleted": 0
            # }
            # data_json = json.dumps(data)
            # default = await self.post_data(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan', data_json)
            # print(default)

    async def set_is_running(self, name, plan_data, is_running):
        data = {
            "name": name,
            "details": plan_data,
            "user": 'admin',
            "is_running": is_running,
            "is_unloading": 1
        }
        data_json = json.dumps(data)
        async with aiohttp.ClientSession() as session:
            res = await self.put_data(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan', data_json)
        await asyncio.sleep(1.0)

    async def set_current_step(self):
        ##needs to save file with current step
        data = {
            "name": self.plan["plan_filename"],
            "details": self.plan,
            "user": 'admin',
            "is_running": 1, 
            "is_unloading": 1,
        }
        data_json = json.dumps(data)

        async with aiohttp.ClientSession() as session:
            res = await self.put_data(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan', data_json)
        await asyncio.sleep(1.0)
        print("++++++++++++++++++++SETTING CURRENT STEP ", res)

    async def load_new_plan(self, name):
        '''Checks last_running is not the same, if it is, fine, just less steps. Loads this new plan via API call, sets new plan is_running=1'''
        try:
            if self.plan["plan_filename"] != "" and self.plan["plan_filename"] != name:
                await self.set_is_running(self.plan["plan_filename"], self.plan, 0)
                
            async with aiohttp.ClientSession() as session:
                data = await self.fetch(session,f'http://192.168.122.225:8000/manage_plan/api/v0.1/plan?plan_name={name}')
            # await asyncio.sleep(1.0)
            data_new = json.loads(data)
            #########TODO:Exceptions
            await self.set_is_running(name, data_new["details"], 1)
            new_plan = data_new["details"]
            if not isinstance(new_plan, dict):
                raise ValueError("Plan should be a dictionary")
            # print(" GOINNG TO VALIDATION")
            # valid = self.validate_plan(True, new_plan)
            # print("IS IT VALIDE ", valid)
            steps = {}
            last_step = len(new_plan["steps"])
            for i in range(last_step):
                # Note: Serializing through JSON turns all dictionary keys into strings. We
                #  need to turn bank numbers and plan steps back into integers for compatibility
                #  with the rest of the code
                row = i + 1
                if str(row) not in new_plan["steps"]:
                    raise ValueError(f"Plan is missing step {row}")
                allsteps = new_plan["steps"]
                step = allsteps[str(row)]
                if "banks" not in step:
                    raise ValueError(f"Plan row {row} is missing 'banks' key")
                if "reference" not in step:
                    raise ValueError(f"Plan row {row} is missing 'reference' key")
                if "duration" not in step:
                    raise ValueError(f"Plan row {row} is missing 'duration' key")
                steps[row] = {
                    "banks": {int(bank_str): step["banks"][bank_str]
                        for bank_str in step["banks"]},
                    "reference": step["reference"],
                    "duration": step["duration"]
                }
            self.set_plan(["plan_filename"], new_plan["plan_filename"])
            self.set_plan(["current_step"], new_plan["current_step"])
            self.set_plan(["steps"], steps)
            self.set_plan(["last_step"], last_step)
            self.set_plan(["focus"], {"row": last_step + 1, "column": 1})
            self.set_plan(["bank_names"], new_plan["bank_names"])
            self.last_running = name
            self.last_running_details = new_plan
            self.postFIFO(Event(Signal.PLAN_LOADED, None))
        except Exception:
            self.postFIFO(Event(Signal.PLAN_LOAD_FAILED, None))



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

    def change_name_bank(self, msg):
        if "bank_names" in msg:
            banks = msg["bank_names"]
            b1 = banks["1"]["name"]
            b2 = banks["2"]["name"]
            b3 = banks["3"]["name"]
            b4 = banks["4"]["name"]
            channels1 = banks["1"]["channels"]
            channels2 = banks["2"]["channels"]
            channels3 = banks["3"]["channels"]
            channels4 = banks["4"]["channels"]

            self.set_plan(
                ["bank_names"], {
                    "1": {
                        "name": b1,
                        "channels": channels1
                    },
                    "2": {
                        "name": b2,
                        "channels": channels2
                    },
                    "3": {
                        "name": b3,
                        "channels": channels3
                    },
                    "4": {
                        "name": b4,
                        "channels": channels4
                    }
                })

    @state
    def _initial(self, e):
        self.publish_errors = True
        self.bank = None
        self.banks_to_process = []
        self.plan_error = None
        self.plan_step_te = TimeEvent("PLAN_STEP_TIMER")
        self.plan_step_timer_target = 0
        self.filename_to_delete = ""
        self.state_after_delete = self._plan_load
        self.button_states = {}
        self.buttons_disabled = False
        self.clean_button_states = {}

        # Keyed by bank. Its values are the masks corresponding to active channels
        # e.g. {1: 0, 2:64, 3:0, 4:0} represents channel active 7 in bank 2
        self.chan_active = {1: 0, 2: 0, 3: 0, 4: 0}
        self.clean_active = {1: 0, 2: 0, 3: 0, 4: 0}
        self.reference_active = None
        Signal.register("PLAN_LOAD_SUCCESSFUL")
        Signal.register("PLAN_LOADED")
        Signal.register("PLAN_LOAD_FAILED")
        Signal.register("PLAN_SAVE_SUCCESSFUL")
        Signal.register("PLAN_SAVE_FAILED")
        Signal.register("PROCEED")
        Framework.subscribe("PIGLET_REQUEST", self)
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("BTN_STANDBY", self)
        Framework.subscribe("BTN_IDENTIFY", self)
        Framework.subscribe("BTN_PLAN", self)
        Framework.subscribe("BTN_PLAN_CANCEL", self)
        Framework.subscribe("BTN_PLAN_CLEAR", self)
        Framework.subscribe("BTN_PLAN_DELETE", self)
        Framework.subscribe("BTN_PLAN_DELETE_FILENAME", self)
        Framework.subscribe("BTN_PLAN_INSERT", self)
        Framework.subscribe("BTN_PLAN_LOAD", self)
        Framework.subscribe("BTN_PLAN_LOAD_CANCEL", self)
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
        Framework.subscribe("MODAL_STEP_1", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("TERMINATE", self)
        Framework.subscribe("ERROR", self)
        Framework.subscribe("BTN_EDIT", self)
        Framework.subscribe("CHANGE_NAME_BANK", self)
        Framework.subscribe("EDIT_CANCEL", self)
        Framework.subscribe("EDIT_SAVE", self)
        Framework.subscribe("BTN_PLAN_LOOP", self)
        Framework.subscribe("BTN_PLAN_RUN", self)
        Framework.subscribe("PERFORM_VALVE_TRANSITION", self)
        Framework.subscribe("VALVE_TRANSITION_DONE", self)
        Framework.subscribe("BTN_LOAD", self)
        Framework.subscribe("BTN_LOAD_CANCEL", self)
        Framework.subscribe("LOAD_FILENAME", self)
        Framework.subscribe("LOAD_MODAL_OK", self)
        Framework.subscribe("LOAD_MODAL_CANCEL", self)
        Framework.subscribe("FILENAME_OK", self)
        Framework.subscribe("FILENAME_CANCEL", self)
        self.te = TimeEvent("UI_TIMEOUT")
        return self.tran(self._configure)

    def disable_buttons(self):
        button_list = ["standby", "identify", "run", "plan", "plan_run", "load", "plan_loop", "reference", "edit"]
        self.button_states = {}
        self.clean_button_states = {}
        for button in button_list:
            self.button_states[button] = self.status[button]
            self.set_status([button], UiStatus.DISABLED)
        for bank in self.all_banks:
            self.clean_button_states[bank] = self.status["clean"][bank]
            self.set_status(["clean", bank], UiStatus.DISABLED)
        self.buttons_disabled = True

    def disable_channel_buttons(self):
        self.channel_button_states = {}
        for bank in self.all_banks:
            for j in range(self.num_chans_per_bank):
                self.channel_button_states[j+1] = self.status["channel"][bank][j + 1]
                self.set_status(["channel", bank, j + 1], UiStatus.DISABLED)

    def restore_buttons(self):
        for button in self.button_states:
            self.set_status([button], self.button_states[button])
        for bank in self.clean_button_states:
            self.set_status(["clean", bank], self.clean_button_states[bank])
        self.buttons_disabled = False

    def restore_channel_buttons(self):
        for bank in self.all_banks:
            for channel in self.channel_button_states:
                self.set_status(["channel", bank, channel], self.channel_button_states[channel])

    def log_transition(self, payload):
        """Log valve transition to clean, reference, exhaust, and control states.
        Currently the control states correspond to a single port (i.e. a bank 
        and channel combination) but in the future, any collection of ports may be
        enabled"""
        if payload.new_valve in ("exhaust", "reference"):
            log.info(f"Activating {payload.new_valve} valve.")
        elif payload.new_valve == "clean":
            for bank in payload.new_settings:
                if payload.new_settings[bank]:
                    log.info(f"Activating clean valve on bank {bank}.")
        elif payload.new_valve == "control":
            for bank in payload.new_settings:
                valve_mask = payload.new_settings[bank]
                # Find first set bit to give channel in bank
                if valve_mask != 0:
                    valve_pos = (valve_mask & (-valve_mask)).bit_length()
                    log.info(f"Activating bank {bank}, channel {valve_pos}.")

    @state
    def _configure(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["standby"], UiStatus.DISABLED)
            self.set_status(["identify"], UiStatus.DISABLED)
            self.set_status(["run"], UiStatus.DISABLED)
            self.set_status(["plan"], UiStatus.DISABLED)
            self.set_status(["load"], UiStatus.DISABLED)
            self.set_status(["plan_run"], UiStatus.DISABLED)
            self.set_status(["plan_loop"], UiStatus.DISABLED)
            self.set_status(["reference"], UiStatus.DISABLED)
            self.set_status(["edit"], UiStatus.DISABLED)
            self.set_status(["timer"], 0)
        elif sig == Signal.SYSTEM_CONFIGURE:
            payload = e.value
            self.all_banks = payload.bank_list
            self.run_async(self.save_port_history())
            self.run_async(self.get_available_plans())
            self.run_async(self.get_last_running())
            return self.tran(self._operational)
        elif sig == Signal.TERMINATE:
            self.run_async(self.db_writer.close_connection())
            return self.tran(self._exit)
        return self.super(self.top)

    @state
    def _operational(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["standby"], UiStatus.READY)
            self.set_status(["identify"], UiStatus.READY)
            self.set_status(["run"], UiStatus.DISABLED)
            self.set_status(["plan"], UiStatus.DISABLED)
            self.set_status(["load"], UiStatus.READY)
            self.set_status(["plan_run"], UiStatus.DISABLED)
            self.set_status(["plan_loop"], UiStatus.DISABLED)
            self.set_status(["reference"], UiStatus.READY)
            self.set_status(["edit"], UiStatus.READY)
            self.set_status(["timer"], 0)
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
        elif sig == Signal.BTN_STANDBY:
            if self.status["standby"] != UiStatus.DISABLED:
                log.debug("Entering Standby State")
                return self.tran(self._standby)
        elif sig == Signal.BTN_IDENTIFY:
            if self.status["identify"] != UiStatus.DISABLED:
                log.debug("Entering Identify State")
                return self.tran(self._identify)
        elif sig == Signal.BTN_RUN:
            if self.status["run"] != UiStatus.DISABLED:
                log.debug("Entering Run State")
                return self.tran(self._run)
        elif sig == Signal.BTN_PLAN:
            if self.status["plan"] != UiStatus.DISABLED:
                log.debug("Entering Plan State")
                return self.tran(self._plan)
        elif sig == Signal.BTN_LOAD:
            if self.status["load"] != UiStatus.DISABLED:
                log.debug("Entering Load State")
                return self.tran(self._load)
        elif sig == Signal.BTN_PLAN_RUN:
            if self.status["plan_run"] != UiStatus.DISABLED:
                log.debug("Entering Plan Run State")
                return self.tran(self._run_plan)
        elif sig == Signal.BTN_PLAN_LOOP:
            if self.status["plan_loop"] != UiStatus.DISABLED:
                log.debug("Entering Plan Loop State")
                return self.tran(self._loop_plan)
        elif sig == Signal.BTN_REFERENCE:
            if self.status["reference"] != UiStatus.DISABLED:
                log.debug("Entering Reference State")
                return self.tran(self._reference)
        elif sig == Signal.BTN_CLEAN:
            if self.status["clean"][e.value["bank"]] != UiStatus.DISABLED:
                log.debug("Entering Clean State")
                self.bank = e.value["bank"]
                return self.tran(self._clean)
        elif sig == Signal.BTN_EDIT:
            if not self.buttons_disabled:
                return self.tran(self._edit)
        elif sig == Signal.ERROR:
            payload = e.value
            self.handle_error_signal(time.time(), payload)
            return self.handled(e)
        elif sig == Signal.PERFORM_VALVE_TRANSITION:
            self.log_transition(e.value)
            return self.handled(e)
        return self.super(self._configure)

    @state
    def _standby(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            self.set_status(["standby"], UiStatus.READY)
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
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("exhaust")))
            self.disable_buttons()
            self.set_status(["standby"], UiStatus.ACTIVE)
            self.set_status(["timer"], 0)
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            return self.tran(self._standby2)
        return self.super(self._standby)

    @state
    def _standby2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["standby"], UiStatus.ACTIVE)
            self.set_status(["timer"], 0)
            return self.handled(e)
        return self.super(self._standby)

    @state
    def _reference(self, e):
        sig = e.signal
        if sig == Signal.EXIT:
            self.set_status(["reference"], UiStatus.READY)
            for bank in self.all_banks:
                self.set_status(["bank", bank], UiStatus.READY)
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
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("reference")))
            self.disable_buttons()
            self.set_status(["reference"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
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
        if sig == Signal.ENTRY:
            self.set_status(["clean", self.bank], UiStatus.CLEAN)
            return self.handled(e)
        elif sig == Signal.EXIT:
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", bank], UiStatus.READY)
                self.set_status(["bank", bank], UiStatus.READY)
                self.clean_active[bank] = 0
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._clean1)
        return self.super(self._operational)

    @state
    def _clean1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            banks_to_clean = {bank: (bank == self.bank) for bank in self.all_banks}
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("clean", banks_to_clean)))
            self.disable_buttons()
            self.set_status(["clean", self.bank], UiStatus.CLEAN)
            self.clean_active[self.bank] = 1
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            return self.tran(self._clean2)
        return self.super(self._clean)

    @state
    def _clean2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            # Use 1-origin for numbering banks and channels
            self.set_status(["clean", self.bank], UiStatus.CLEAN)
            self.set_status(["bank", self.bank], UiStatus.CLEAN)
            return self.handled(e)
        return self.super(self._clean)

    @state
    def _identify(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("exhaust")))
            self.disable_buttons()
            self.set_status(["identify"], UiStatus.ACTIVE)
            self.banks_to_process = self.all_banks.copy()
            self.bank = self.banks_to_process.pop(0)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["identify"], UiStatus.READY)
            self.set_status(["standby"], UiStatus.READY)
            self.set_status(["run"], UiStatus.READY)
            self.set_status(["plan"], UiStatus.READY)
            self.set_status(["load"], UiStatus.READY)
            self.set_status(["reference"], UiStatus.READY)
            self.set_status(["timer"], 0)
            for bank in self.all_banks:
                # Use 1-origin for numbering banks and channels
                self.set_status(["clean", bank], UiStatus.READY)
                self.set_status(["bank", bank], UiStatus.READY)
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            return self.tran(self._identify1)
        elif sig == Signal.BTN_IDENTIFY:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _identify1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("IDENTIFY", [self.bank])))
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
            if e.value[self.bank]['OPSTATE'].startswith('ident'):
                return self.tran(self._identify3)
        return self.super(self._identify)

    @state
    def _identify3(self, e):
        sig = e.signal
        if sig == Signal.PIGLET_STATUS:
            if e.value[self.bank]['OPSTATE'] == 'standby':
                return self.tran(self._identify4)
            return self.handled(e)
        return self.super(self._identify)

    @state
    def _identify4(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PIGLET_REQUEST, PigletRequestPayload("ACTIVECH?", [self.bank])))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            msg = int(e.value[self.bank])  # Integer representing available channels
            self.set_available_ports(["available_ports", str(self.bank)], msg)
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
                self.restore_buttons()
                # Otherwise, enable run and plan buttons and go back to standby since identification is complete
                self.set_status(["run"], UiStatus.READY)
                self.set_status(["plan"], UiStatus.READY)
                # Write out bank name and port availability information to database
                self.run_async(self.save_port_history())
                return self.tran(self._operational)
        return self.super(self._identify)

    @state
    def _plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for bank in self.all_banks:
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.AVAILABLE:
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
            return self.handled(e)
        elif sig == Signal.EXIT:
            for bank in self.all_banks:
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.READY:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            # self.set_plan(["panel_to_show"], int(PlanPanelType.NONE))
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
                    "html": f"<h2 class='test'>Confirm file deletion</h2><p>{msg}</p>",
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
            self.run_async(self.get_plan_filenames())
            return self.tran(self.state_after_delete)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self.state_after_delete)
        return self.super(self._plan)

    @state
    def _plan_plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            # self.set_plan(["panel_to_show"], int(PlanPanelType.PLAN))
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("exhaust")))
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_OK:
            self.plan_error = self.validate_plan(check_avail=True)
            if not self.plan_error.error:
                self.set_status(["plan_run"], UiStatus.READY)
                self.set_status(["plan_loop"], UiStatus.READY)
                return self.tran(self._operational)
            else:
                self.set_status(["plan_run"], UiStatus.DISABLED)
                self.set_status(["plan_loop"], UiStatus.DISABLED)
                return self.tran(self._plan_plan1)
        elif sig == Signal.BTN_PLAN_CANCEL:
            return self.tran(self._operational)
        elif sig == Signal.BTN_PLAN_CLEAR:
            return self.tran(self._plan_clear)
            # self.plan_clear()
            # return self.handled(e)
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
        elif sig == Signal.BTN_CLEAN:
            self.add_bank_to_clean_to_plan(e.value["bank"])
            return self.handled(e)
        elif sig == Signal.BTN_REFERENCE:
            self.add_reference_to_plan()
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
    def _plan_clear(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            msg = "Are you sure you want to Clear Plan?"
            self.set_modal_info([], {
                "show": True,
                "html": f"<h2 class='test'>Clear Plan?</h2><p>{msg}</p>",
                "num_buttons": 2,
                "buttons": {
                    1: {
                        "caption": "Clear Plan",
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
            self.plan_clear()
            return self.tran(self._plan_plan)
        elif sig == Signal.MODAL_CLOSE:
            return self.tran(self._plan_plan)
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
            # self.set_plan(["panel_to_show"], int(PlanPanelType.LOAD))
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
                # self.load_plan_from_file()
                self.postFIFO(Event(Signal.PLAN_LOAD_SUCCESSFUL, None))
            except Exception:
                self.postFIFO(Event(Signal.PLAN_LOAD_FAILED, format_exc()))
            return self.handled(e)
        elif sig == Signal.PLAN_LOAD_SUCCESSFUL:
            self.run_async(self.save_port_history())
            return self.tran(self._plan)
        elif sig == Signal.PLAN_LOAD_FAILED:
            self.plan_error = PlanError(True, f'<div>Unhandled Exception. Please contact support.</div>')
            return self.tran(self._plan_load11)
        return self.super(self._plan_load)

    @state
    def _plan_load11(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_modal_info([], {
                "show": True,
                "html": f"<h3 class='test'>Plan load error</h3><p>{self.plan_error.message}</p>",
                "num_buttons": 0
            })
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
            # self.set_plan(["panel_to_show"], int(PlanPanelType.SAVE))
            self.state_after_delete = self._plan_save
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_SAVE_CANCEL:
            return self.tran(self._plan)
        elif sig == Signal.PLAN_SAVE_FILENAME:
            # Remove non alphanumeric characters
            self.set_plan(["plan_filename"], re.sub(r'[^\w-]', "", e.value["name"]))
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_SAVE_OK:
            self.valid_plan = self.validate_plan_filename(self.plan["plan_filename"])

            if self.valid_plan:
                fname = os.path.join(PLAN_FILE_DIR, self.plan["plan_filename"] + ".pln")
                if os.path.isfile(fname):
                    return self.tran(self._plan_save1)
                else:
                    return self.tran(self._plan_save2)
            else:
                self.set_modal_info([], {
                    "show": True,
                    "html": f"<h3 class='test'>Please Enter a Valid Filename</h3>",
                    "num_buttons": 0
                })
            return self.handled(e)
        return self.super(self._plan_file)

    @state
    def _plan_save1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            msg = "File exists. Overwrite?"
            self.set_modal_info(
                [], {
                    "show": True,
                    "html": f"<h2 class='test'>Confirm file overwrite</h2><p>{msg}</p>",
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
                self.save_plan_to_file(self.plan["plan_filename"])
                self.postFIFO(Event(Signal.PLAN_SAVE_SUCCESSFUL, None))
            except Exception:
                self.postFIFO(Event(Signal.PLAN_SAVE_FAILED, format_exc()))
            return self.handled(e)
        elif sig == Signal.PLAN_SAVE_SUCCESSFUL:
            self.run_async(self.get_plan_filenames())
            return self.tran(self._plan)
        elif sig == Signal.PLAN_SAVE_FAILED:
            self.plan_error = PlanError(True, f'<div>Unhandled Exception. Please contact support.</div>')
            return self.tran(self._plan_save21)
        return self.super(self._plan_save)

    @state
    def _plan_save21(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_modal_info([], {
                "show": True,
                "html": f"<h3 class='test'>Plan save error</h3><p>{self.plan_error.message}</p>",
                "num_buttons": 0
            })
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
                "html": f"<h3 class='test'>Plan error</h3><p>{self.plan_error.message}</p>",
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

    ##Load Button Pressed on Command Panel
    @state
    def _load(self, e):
        print("-----------> _load State")
        sig = e.signal
        if sig == Signal.ENTRY:
            return self.handled(e)
        elif sig == Signal.EXIT:
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._load1)
        elif sig == Signal.BTN_LOAD:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _load1(self, e):
        print("-----------> _load1 State")
        sig = e.signal
        if sig == Signal.ENTRY:
            return self.handled(e)
        elif sig == Signal.BTN_LOAD_CANCEL:
            return self.tran(self._operational)
        elif sig == Signal.LOAD_FILENAME:
            return self.tran(self._load_preview)
        elif sig == Signal.EXIT:
            return self.handled(e)
        return self.super(self._load)

    @state
    def _load_preview(self, e):
        print("--------------> load_preview State")
        sig = e.signal
        if sig == Signal.ENTRY:
            return self.handled(e)
        elif sig == Signal.FILENAME_OK:
            return self.tran(self._load_preview1)
        elif sig == Signal.FILENAME_CANCEL:
            return self.tran(self._load1)
        return self.super(self._load1)

    @state
    def _load_preview1(self, e):
        print("-----------> _load_preview1 State")
        sig = e.signal
        if sig == Signal.ENTRY:
            return self.handled(e)
        elif sig == Signal.LOAD_MODAL_OK:
            #TODO: Validate Plan from here?
            # self.plan_error = self.validate_plan(check_avail=True)
            # if True or not self.plan_error.error:
            self.set_status(["plan_run"], UiStatus.READY)
            self.set_status(["plan_loop"], UiStatus.READY)
            # new_plan = e.value["plan"]
            self.plan_name = e.value["name"]
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("exhaust")))   
            return self.tran(self._load_preview2)
            # else:
            #     #plan error
            #     self.set_status(["plan_run"], UiStatus.DISABLED)
            #     self.set_status(["plan_loop"], UiStatus.DISABLED)
            #     return self.tran(self._load1)
        elif sig == Signal.LOAD_MODAL_CANCEL:
            return self.tran(self._load_preview)
        return self.super(self._load_preview)

    @state
    def _load_preview2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            try:
                self.run_async(self.load_new_plan(self.plan_name))
                self.disable_buttons()
                self.postFIFO(Event(Signal.PLAN_LOAD_SUCCESSFUL, None))
            except Exception:
                self.postFIFO(Event(Signal.PLAN_LOAD_FAILED, format_exc()))
            return self.handled(e)
        elif sig == Signal.PLAN_LOADED:
            self.run_async(self.save_port_history())
            self.restore_buttons()
            print("-----------> Do we get to port histroy?")
            return self.tran(self._operational)
        elif sig == Signal.PLAN_LOAD_FAILED:
            self.restore_buttons()
            print("-----------> Do we get to PLAN FAILTED?")
            self.plan_error = PlanError(True, f'<div>Unhandled Exception. Please contact support.</div>')
            return self.tran(self._load_preview)
        return self.super(self._load_preview)


    @state
    def _sampling(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("exhaust")))
            print("------------> RUNNNIGS")
            self.disable_buttons()
            return self.handled(e)
        elif sig == Signal.EXIT:
            print("GOING TO STANDBY! ")
            self.set_status(["run"], UiStatus.READY)
            self.set_status(["plan"], UiStatus.READY)
            self.set_status(["run_plan"], UiStatus.READY)
            self.set_status(["loop_plan"], UiStatus.READY)
            self.set_status(["load"], UiStatus.READY)
            for bank in self.all_banks:
                if not self.status["bank"][bank] == UiStatus.READY:
                    self.set_status(["bank", bank], UiStatus.READY)
                if not self.status["clean"][bank] == UiStatus.READY:
                    self.set_status(["clean", bank], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] in [UiStatus.READY, UiStatus.ACTIVE]:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            return self.handled(e)
        elif sig == Signal.BTN_RUN:
            return self.tran(self._run1)
        elif sig == Signal.BTN_PLAN_RUN:
            return self.tran(self._run_plan1)
        elif sig == Signal.BTN_PLAN_LOOP:
            return self.tran(self._loop_plan1)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            self.postFIFO(Event(Signal.PROCEED, None))
        return self.super(self._operational)

    @state
    def _run(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["run"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["run"], UiStatus.READY)
            return self.handled(e)
        elif sig == Signal.BTN_RUN:
            return self.handled(e)
        elif sig == Signal.PROCEED:
            return self.tran(self._run1)
        return self.super(self._sampling)

    @state
    def _run1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for bank in self.all_banks:
                if not self.status["bank"][bank] == UiStatus.READY:
                    self.set_status(["bank", bank], UiStatus.READY)
                if not self.status["clean"][bank] == UiStatus.READY:
                    self.set_status(["clean", bank], UiStatus.READY)
                if not self.status["reference"] == UiStatus.READY:
                    self.set_status(["reference"], UiStatus.READY)
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.AVAILABLE:
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
            return self.handled(e)
        elif sig == Signal.EXIT:
            for bank in self.all_banks:
                for j in range(self.num_chans_per_bank):
                    if self.status["channel"][bank][j + 1] == UiStatus.READY:
                        self.set_status(["channel", bank, j + 1], UiStatus.AVAILABLE)
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run11)
        return self.super(self._run)

    @state
    def _run11(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["run"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.BTN_CHANNEL:
            if self.status["channel"][e.value["bank"]][e.value["channel"]] == UiStatus.READY:
                mask = 1 << (e.value["channel"] - 1)
                # For this version, we can only have one active channel, so
                #  replace the currently active channel with the selected one
                for bank in self.all_banks:
                    # Turn off ACTIVE states in UI for active channels
                    for j in setbits(self.chan_active[bank]):
                        self.set_status(["channel", bank, j + 1], UiStatus.READY)
                    # Replace with the selected channel
                    if bank == e.value["bank"]:
                        self.chan_active[bank] = mask
                    else:
                        self.chan_active[bank] = 0
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("control", self.chan_active)))
                self.disable_channel_buttons()
                self.disable_buttons()
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            self.restore_channel_buttons()
            for bank in self.all_banks:
                mask = self.chan_active[bank]
                for j in setbits(mask):
                    self.set_status(["channel", bank, j + 1], UiStatus.ACTIVE)
            return self.handled(e)
        return self.super(self._run1)

    @state
    def _run_plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["load"], UiStatus.DISABLED)
            self.set_status(["plan_run"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["plan_run"], UiStatus.READY)
            self.set_status(["timer"], 0)
            self.timer = False
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_RUN:
            return self.handled(e)
        elif sig == Signal.PROCEED:
            return self.tran(self._run_plan1)
        return self.super(self._sampling)

    @state
    def _run_plan1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            print("PLAN RUNNING ------------------->")
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_OK:
            print("_________________________________> STEP ", self.plan["current_step"])
            self.run_async(self.save_plan_to_default())
            self.plan_step_timer_target = asyncio.get_event_loop().time()
            return self.tran(self._run_plan2)
        elif sig == Signal.MODAL_STEP_1:
            #set step to #1
            self.set_plan(["current_step"], 1)
            self.run_async(self.save_plan_to_default())
            self.plan_step_timer_target = asyncio.get_event_loop().time()
            return self.tran(self._run_plan2)
        elif sig == Signal.MODAL_CLOSE:
            #SET CURRENT_STEP
            return self.tran(self._operational)
        return self.super(self._run_plan)

    @state
    def _run_plan2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["load"], UiStatus.DISABLED)
            self.set_status(["plan_run"], UiStatus.ACTIVE)
            current_step = self.plan["current_step"]
            timer = self.plan["steps"][current_step]["duration"]
            self.plan_step_timer_target += self.plan["steps"][current_step]["duration"]
            self.set_status(["timer"], timer)
            self.plan_step_te.postAt(self, self.plan_step_timer_target)
            return self.handled(e)
        elif sig == Signal.EXIT:
            print("LEAVVING")
            self.run_async(self.set_current_step())
            self.run_async(self.save_plan_to_default())
            self.plan_step_te.disarm()
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run_plan21)
        elif sig == Signal.PLAN_STEP_TIMER:
            current_step = self.plan["current_step"]
            last_step = self.plan["last_step"]
            current_step += 1
            if current_step > last_step:
                current_step -= last_step
                self.set_plan(["current_step"], current_step)
                # All steps done
                #SET CURRENT_STEP
                self.run_async(self.set_current_step())
                return self.tran(self._operational)
            else:
                self.set_plan(["current_step"], current_step)
                return self.tran(self._run_plan2)
        return self.super(self._run_plan)

    @state
    def _run_plan21(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            current_step = self.plan["current_step"]
            bank_config = self.plan["steps"][current_step]["banks"]
            self.reference_active = self.plan["steps"][current_step]["reference"]
            for bank in self.all_banks:
                self.clean_active[bank] = bank_config[bank]["clean"]
                self.chan_active[bank] = bank_config[bank]["chan_mask"]
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._run_plan211)
        elif sig == Signal.PIGLET_STATUS:
            # Update the channel button states on the UI from SOLENOID_VALVES in piglet status
            result = {}
            for bank in self.all_banks:
                if self.reference_active:
                    self.set_status(["clean", bank], UiStatus.READY)
                    self.set_status(["bank", bank], UiStatus.REFERENCE)
                elif e.value[bank]['OPSTATE'] == "clean":
                    self.set_status(["clean", bank], UiStatus.CLEAN)
                    self.set_status(["bank", bank], UiStatus.CLEAN)
                else:
                    self.set_status(["clean", bank], UiStatus.READY)
                    self.set_status(["bank", bank], UiStatus.READY)

                mask = e.value[bank]['SOLENOID_VALVES']
                sel = setbits(mask)
                chan_status = self.status["channel"][bank].copy()
                for j in range(self.num_chans_per_bank):
                    current = chan_status[j + 1]
                    if current != UiStatus.DISABLED:
                        if j in sel:
                            if current != UiStatus.ACTIVE:
                                chan_status[j + 1] = UiStatus.ACTIVE
                        else:
                            if current != UiStatus.AVAILABLE:
                                chan_status[j + 1] = UiStatus.AVAILABLE
                result[bank] = chan_status
            self.set_status(["channel"], result)
            return self.handled(e)
        return self.super(self._run_plan2)

    @state
    def _run_plan211(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            some_clean_active = any([self.clean_active[bank] for bank in self.clean_active])
            if self.reference_active:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("reference")))
            elif some_clean_active:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("clean", self.clean_active)))
            else:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("control", self.chan_active)))
            self.disable_buttons()
            self.timer = True
            self.run_async(self.timer_update())
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            return self.handled(e)
        return self.super(self._run_plan21)

    @state
    def _loop_plan(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["plan_loop"], UiStatus.ACTIVE)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_status(["plan_loop"], UiStatus.READY)
            self.timer = False
            self.set_status(["timer"], 0)
            return self.handled(e)
        elif sig == Signal.BTN_PLAN_LOOP:
            return self.handled(e)
        elif sig == Signal.PROCEED:
            return self.tran(self._loop_plan1)
        return self.super(self._sampling)

    @state
    def _loop_plan1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.set_modal_info(["show"], False)
            return self.handled(e)
        elif sig == Signal.MODAL_OK:
            print("-----------------> Signal Modal OK")
            self.run_async(self.save_plan_to_default())
            self.plan_step_timer_target = asyncio.get_event_loop().time()
            return self.tran(self._loop_plan2)
        elif sig == Signal.MODAL_STEP_1:
            print("-----------------> Signal Modal Step 1")
            self.set_plan(["current_step"], 1)
            self.run_async(self.save_plan_to_default())
            self.plan_step_timer_target = asyncio.get_event_loop().time()
            return self.tran(self._loop_plan2)
        elif sig == Signal.MODAL_CLOSE:
            print("-----------------> Signal Modal Cancel")
            return self.tran(self._operational)
        return self.super(self._loop_plan)

    @state
    def _loop_plan2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.set_status(["load"], UiStatus.DISABLED)
            self.set_status(["plan_loop"], UiStatus.ACTIVE)
            current_step = self.plan["current_step"]
            print("_______________________> cureent step ", current_step)
            timer = self.plan["steps"][current_step]["duration"]
            self.plan_step_timer_target += self.plan["steps"][current_step]["duration"]
            self.set_status(["timer"], timer)
            self.plan_step_te.postAt(self, self.plan_step_timer_target)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.run_async(self.set_current_step())
            self.run_async(self.save_plan_to_default())
            self.plan_step_te.disarm()
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._loop_plan21)
        elif sig == Signal.PLAN_STEP_TIMER:
            current_step = self.plan["current_step"]
            last_step = self.plan["last_step"]
            current_step += 1
            if current_step > last_step:
                current_step -= last_step
            self.set_plan(["current_step"], current_step)
            self.run_async(self.set_current_step())
            return self.tran(self._loop_plan2)
        return self.super(self._loop_plan)

    @state
    def _loop_plan21(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            current_step = self.plan["current_step"]
            bank_config = self.plan["steps"][current_step]["banks"]
            self.reference_active = self.plan["steps"][current_step]["reference"]
            for bank in self.all_banks:
                self.clean_active[bank] = bank_config[bank]["clean"]
                self.chan_active[bank] = bank_config[bank]["chan_mask"]
            return self.handled(e)
        elif sig == Signal.INIT:
            return self.tran(self._loop_plan211)
        elif sig == Signal.PIGLET_STATUS:
            # Update the channel button states on the UI from SOLENOID_VALVES in piglet status
            result = {}
            for bank in self.all_banks:
                if self.reference_active:
                    self.set_status(["clean", bank], UiStatus.READY)
                    self.set_status(["bank", bank], UiStatus.REFERENCE)
                elif e.value[bank]['OPSTATE'] == "clean":
                    self.set_status(["clean", bank], UiStatus.CLEAN)
                    self.set_status(["bank", bank], UiStatus.CLEAN)
                else:
                    self.set_status(["clean", bank], UiStatus.READY)
                    self.set_status(["bank", bank], UiStatus.READY)

                mask = e.value[bank]['SOLENOID_VALVES']
                sel = setbits(mask)
                chan_status = self.status["channel"][bank].copy()
                for j in range(self.num_chans_per_bank):
                    current = chan_status[j + 1]
                    if current != UiStatus.DISABLED:
                        if j in sel:
                            if current != UiStatus.ACTIVE:
                                chan_status[j + 1] = UiStatus.ACTIVE
                        else:
                            if current != UiStatus.AVAILABLE:
                                chan_status[j + 1] = UiStatus.AVAILABLE
                result[bank] = chan_status
            self.set_status(["channel"], result)
            return self.handled(e)
        return self.super(self._loop_plan2)

    @state
    def _loop_plan211(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            some_clean_active = any([self.clean_active[bank] for bank in self.clean_active])
            if self.reference_active:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("reference")))
            elif some_clean_active:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("clean", self.clean_active)))
            else:
                Framework.publish(Event(Signal.PERFORM_VALVE_TRANSITION, ValveTransitionPayload("control", self.chan_active)))
            self.disable_buttons()
            self.timer = True
            self.run_async(self.timer_update())
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            self.restore_buttons()
            return self.handled(e)
        return self.super(self._loop_plan21)

    @state
    def _edit(self, e):
        sig = e.signal
        if sig == Signal.INIT:
            return self.tran(self._edit_edit)
        elif sig == Signal.EXIT:
            # self.set_plan(["panel_to_show"], int(PlanPanelType.NONE))
            return self.handled(e)
        elif sig == Signal.BTN_EDIT:
            return self.handled(e)
        return self.super(self._operational)

    @state
    def _edit_edit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            # self.set_plan(["panel_to_show"], int(PlanPanelType.EDIT))
            return self.handled(e)
        elif sig == Signal.EDIT_CANCEL:
            # self.set_plan(["panel_to_show"], int(PlanPanelType.NONE))
            return self.tran(self._operational)
        elif sig == Signal.EDIT_SAVE:
            print("SAVIN ++++++++++++++++++++++++==")
            self.change_name_bank(e.value)
            self.run_async(self.save_port_history())
            # self.set_plan(["panel_to_show"], int(PlanPanelType.NONE))
            return self.tran(self._operational)
        return self.super(self._edit)

    async def click_button(self, button_name, button_signal, msg="Timeout", timeout=5.0):
        time_elapsed = 0
        while self.get_status()[button_name] != UiStatus.READY:
            await asyncio.sleep(0.5)
            time_elapsed += 0.5
            if time_elapsed > timeout:
                raise TimeoutError(msg)
        Framework.publish(Event(button_signal, None))

    async def wait_for_state(self, state, msg="Timeout", timeout=5.0):
        time_elapsed = 0
        while self.state != state:
            await asyncio.sleep(0.5)
            time_elapsed += 0.5
            if time_elapsed > timeout:
                raise TimeoutError(msg)

    async def auto_setup_flow(self, plan_filename_no_ext=None):
        """This runs the channel identification procedure and then loops a plan specified
        in `plan_filename_no_ext` starting at the first row. It can be called from the
        supervisor shortly after startup to start the flow through the rack on power-up.
        """
        # if plan_filename_no_ext is not None:
        #     fname = os.path.join(PLAN_FILE_DIR, f"{plan_filename_no_ext}.pln")
        #     if not os.path.exists(fname):
        #         plan_filename_no_ext = None
        #         log.warning(f"Startup plan file {fname} not found")
        # if self.last_running is not "":
        #     async with aiohttp.ClientSession() as session:
        #         default_plan = await self.fetch(session, 'http://192.168.122.225:8000/manage_plan/api/v0.1/plan?plan_name=__default__')
        #     plan = json.loads(default_plan)

        #get last running plan
        # self.run_async(self.get_last_running())

        try:
            if self.get_status()["standby"] != UiStatus.ACTIVE:
                await self.click_button("standby", Signal.BTN_STANDBY, "Timeout waiting for STANDBY button")
            await self.click_button("identify", Signal.BTN_IDENTIFY, "Timeout waiting for IDENTIFY button")
            await asyncio.sleep(1.0)
            # Wait until we are out of the identify state
            while self.get_status()["standby"] != UiStatus.ACTIVE:
                await asyncio.sleep(1.0)
            if plan_filename_no_ext is not None:
                await self.click_button("load", Signal.BTN_LOAD, "Timeout waiting to load default plan")
                await self.wait_for_state(self._load1, "Timeout reaching _load state before loading plan file")
                Framework.publish(Event(Signal.LOAD_FILENAME, None))
                await self.wait_for_state(self._load_preview, "Timeout reaching _load_preview state")
                Framework.publish(Event(Signal.FILENAME_OK, None))
                await self.wait_for_state(self._load_preview1, "Timeout reaching _load_preview1 state")
                Framework.publish(Event(Signal.LOAD_MODAL_OK, {"name": self.last_running}))
                await self.wait_for_state(self._load_preview2, "Timeout reaching _load_preview2 state")

                ##SET Current Step to 1
                ##loads plan
                await asyncio.sleep(1.0)
                await self.click_button("plan_loop", Signal.BTN_PLAN_LOOP, "Timeout waiting to start default plan")
                await asyncio.sleep(1.0)
                await self.wait_for_state(self._loop_plan1, "Timeout reaching _loop_plan1 state")
                Framework.publish(Event(Signal.MODAL_OK, None))

                # await self.click_button("plan", Signal.BTN_PLAN, "Timeout waiting to load default plan")
                # await self.wait_for_state(self._plan_plan, "Timeout reaching _plan_plan state before loading plan file")
                # Framework.publish(Event(Signal.BTN_PLAN_LOAD, None))
                # await self.wait_for_state(self._plan_load, "Timeout reaching _plan_load state")
                # Framework.publish(Event(Signal.PLAN_LOAD_FILENAME, {"name": plan_filename_no_ext}))
                # await self.wait_for_state(self._plan_plan, "Timeout reaching _plan_plan state")
                # Framework.publish(Event(Signal.PLAN_PANEL_UPDATE, {"current_step": 1}))
                # await asyncio.sleep(1.0)
                # Framework.publish(Event(Signal.BTN_PLAN_OK, None))
                # await self.click_button("plan_loop", Signal.BTN_PLAN_LOOP, "Timeout waiting to start default plan")
                # await asyncio.sleep(1.0)
                # await self.wait_for_state(self._loop_plan1, "Timeout reaching _loop_plan1 state")
                # Framework.publish(Event(Signal.MODAL_OK, None))
        except TimeoutError as e:
            log.warning(repr(e))
            return repr(e)

        msg = "Successfully initialized flow state"
        log.debug(msg)
        return msg
