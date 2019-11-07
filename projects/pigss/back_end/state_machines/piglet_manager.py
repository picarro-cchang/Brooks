#!/usr/bin/env python3
"""
The piglet manager is a Hierarchical State Machine which communicates with a number
 of piglets (or piglet simulators) and gathers information from them periodically.
 This information is used to control the MFC and valves on the rack (notably the
 exhaust and reference valves) via calls to the appropriate drivers.
"""
import asyncio
import time

from async_hsm import Ahsm, Event, Framework, Signal, TimeEvent, state
from back_end.state_machines.pigss_payloads import (PigletRequestPayload, SystemConfiguration, ValvePositionPayload)

POLL_PERIOD = 0.5


class PigletManager(Ahsm):
    """
    The manager is written as an HSM with a single "_manager" state which handles
    events of types PIGLET_REQUEST and PIGLET_STATUS_TIMER.

    When a PIGLET_REQUEST event arrives, its payload is of type PigletRequestPayload. This
    contains a command that is to be sent to one or more piglets specified by bank_list.
    The send_to_piglets method sends the command to the specified piglets and gathers the
    results into a dictionary keyed by bank. It generates a PIGLET_RESPONSE event with a
    dictionary containing the responses keyed by bank.

    When a PIGLET_STATUS_TIMER event arrives, the coroutine get_status is performed which
    send a collection of requests to all the piglets (specified in self.bank_list). These
    data are aggregated into a dictionary keyed by bank. The values are themselves dictionaries,
    consisting of the status data obtained from the piglet. An timestamp (from Unix epoch)
    is included in the result dictionary. It generates a PIGLET_STATUS event.

    A lock (self.comm_lock) is used to ensure that status discovery and piglet requests do not
    occur at the same time.
    """

    def __init__(self, farm):
        super().__init__()
        self.farm = farm
        self.bank_list = None
        self.mad_mapper_result = None
        self.picarro_analyzers = []
        self.comm_lock = asyncio.Lock()
        self.status_lock = asyncio.Lock()
        self.valve_mask = 0
        self.clean_mask = 0
        self.tasks = []

    @state
    def _initial(self, e):
        self.mfc_override = None
        self.publish_errors = True
        self.piglet_status_te = TimeEvent("PIGLET_STATUS_TIMER")
        Framework.subscribe("MFC_SET", self)
        Framework.subscribe("PERFORM_VALVE_TRANSITION", self)
        Framework.subscribe("PIGLET_REQUEST", self)
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("VALVE_POSITION", self)
        Framework.subscribe("VALVE_TRANSITION_DONE", self)
        Framework.subscribe("TERMINATE", self)
        self.old_valve = "exhaust"
        self.old_settings = {}
        return self.tran(self._configure)

    @state
    def _configure(self, e):
        sig = e.signal
        if sig == Signal.SYSTEM_CONFIGURE:
            # Received configuration information. This also means that supervised processes have started,
            # so the async wrapped RPC servers are also accessible
            payload = e.value
            self.bank_list = payload.bank_list
            self.mad_mapper_result = payload.mad_mapper_result
            self.picarro_analyzers = [rpc_name for rpc_name in self.farm.RPC if rpc_name.startswith("Picarro_")]
            return self.tran(self._manager)
        return self.super(self.top)

    @state
    def _manager(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            now = time.time()
            # Call handle_valve_position to establish the valve_pos tag and valve_stable_time field
            #  in the data
            self.run_async(self.handle_valve_position(ValvePositionPayload(time=now, valve_pos=0, valve_mask=0, clean_mask=0)))
            self.piglet_status_te.postEvery(self, POLL_PERIOD)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.piglet_status_te.disarm()
            return self.handled(e)
        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)
        elif sig == Signal.PIGLET_REQUEST:
            payload = e.value
            self.run_async(self.send_to_piglets(payload.command, payload.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS_TIMER:
            self.run_async(self.get_status(self.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS:
            piglet_status = e.value
            mfc_total = 0
            for bank in self.bank_list:
                mfc_total += piglet_status[bank]["MFCVAL"]
            self.run_async(self.handle_piglet_status(piglet_status, mfc_total))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            return self.handled(e)
        elif sig == Signal.PERFORM_VALVE_TRANSITION:
            self.run_async(self.perform_valve_transition(e.value))
            return self.handled(e)
        elif sig == Signal.VALVE_TRANSITION_DONE:
            return self.handled(e)
        elif sig == Signal.MFC_SET:
            set_point = e.value['mfc_setpoint']
            self.run_async(self.set_mfc_setpoint(set_point))
            return self.handled(e)
        elif sig == Signal.VALVE_POSITION:
            self.run_async(self.handle_valve_position(e.value))
            return self.handled(e)
        return self.super(self._configure)

    async def handle_piglet_status(self, piglet_status, mfc_total):
        if self.mfc_override is not None:
            mfc_total = self.mfc_override
        when = piglet_status["time"]
        Framework.publish(Event(Signal.MFC_SET, {"time": when, "mfc_setpoint": mfc_total}))

    @state
    def _exit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.terminated = True
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            return self.handled(e)
        return self.super(self.top)

    async def perform_valve_transition(self, valve_transition_payload):
        # Perform a valve transition according to the following protocol:
        # 1) Assert the new valve settings
        # 2) Assert MFC override for new settings if necessary
        # 3) Delay for a specified period
        # 4) Deassert the old valve states
        # 5) Save new settings as old
        old = self.old_valve
        new = valve_transition_payload.new_valve
        new_settings = valve_transition_payload.new_settings
        if new == "exhaust":
            await self.set_exhaust_valve("open")
            self.mfc_override = 0.0
        elif new == "reference":
            await self.set_reference_valve("open")
            self.mfc_override = self.farm.config.get_reference_mfc_flow()
        elif new == "clean":
            banks = [bank for bank in new_settings if new_settings[bank] != 0 and bank in self.bank_list]
            await self.exec_on_banks(lambda bank: self.command_handler("CLEAN", bank), banks)
            rest = [bank for bank in self.bank_list if bank not in banks]
            await self.exec_on_banks(lambda bank: self.command_handler("STANDBY", bank), rest)
            self.mfc_override = None
        elif new == "control":
            for bank in new_settings:
                if bank in self.bank_list:
                    await self.command_handler(f"CHANSET {new_settings[bank]}", bank)
            rest = [bank for bank in self.bank_list if bank not in new_settings]
            await self.exec_on_banks(lambda bank: self.command_handler("STANDBY", bank), rest)
            self.mfc_override = None

        if new == "clean":
            new = "control"
        if old == "clean":
            old = "control"

        if new != old:
            await asyncio.sleep(2.0)
            if old == "exhaust":
                await self.set_exhaust_valve("close")
            elif old == "reference":
                await self.set_reference_valve("close")
            elif old == "control":
                await self.exec_on_banks(lambda bank: self.command_handler("STANDBY", bank), self.bank_list)

        self.old_valve = valve_transition_payload.new_valve
        self.old_settings = valve_transition_payload.new_settings

        Framework.publish(Event(Signal.VALVE_TRANSITION_DONE, valve_transition_payload))

    async def command_handler(self, command, bank):
        return await self.farm.RPC[f"Piglet_{bank}"].send(command)

    async def get_status_of_bank(self, bank):
        status = {}
        status["OPSTATE"] = await self.farm.RPC[f"Piglet_{bank}"].send("OPSTATE?")
        status["IDSTATE"] = await self.farm.RPC[f"Piglet_{bank}"].send("IDSTATE?")
        status["MFCVAL"] = float(await self.farm.RPC[f"Piglet_{bank}"].send("MFCVAL?"))
        status["SOLENOID_VALVES"] = int(await self.farm.RPC[f"Piglet_{bank}"].send("CHANSET?"))
        return status

    async def exec_on_banks(self, coroutine_function, bank_list):
        async with self.comm_lock:
            responses = await asyncio.gather(*[coroutine_function(bank) for bank in bank_list])
            result = {bank: response for bank, response in zip(bank_list, responses)}
            return result

    async def send_to_piglets(self, command, bank_list):
        response = await self.exec_on_banks(lambda bank: self.command_handler(command, bank), bank_list)
        Framework.publish(Event(Signal.PIGLET_RESPONSE, response))

    async def get_status(self, bank_list):
        response = await self.exec_on_banks(self.get_status_of_bank, bank_list)
        mfc_data = await self.farm.RPC["MFC"].get_data_dict()
        response["MFCFLOW"] = float(mfc_data["m_flow"])
        response["EXHAUST"] = "close" if await self.farm.RPC["Relay_0"].NUMATO_get_relay_status(0) else "open"
        response["REFERENCE"] = "open" if await self.farm.RPC["Relay_0"].NUMATO_get_relay_status(1) else "closed"
        now = time.time()
        # Calculate the states of all the solenoid valves
        _valve_mask = 0
        _clean_mask = 0
        # Get the states of all the valves as a 32 bit integer
        for bank in bank_list:
            _valve_mask += response[bank]['SOLENOID_VALVES'] << (8 * (bank - 1))
            if response[bank]["OPSTATE"] == "clean":
                _clean_mask += (1 << bank - 1)
        if _valve_mask != self.valve_mask or _clean_mask != self.clean_mask:
            self.valve_mask = _valve_mask
            self.clean_mask = _clean_mask
            # Find index of first set bit using bit-twiddling hack
            valve_pos = (_valve_mask & (-_valve_mask)).bit_length()
            Framework.publish(Event(Signal.VALVE_POSITION, ValvePositionPayload(now, valve_pos, self.valve_mask, self.clean_mask)))
        response["time"] = now
        Framework.publish(Event(Signal.PIGLET_STATUS, response))

    async def handle_valve_position(self, valve_pos_payload):
        # We need to add a tag for valve_pos as well as set up the field valve_stable_time
        #  for each analyzer
        for analyzer_rpc_name in self.picarro_analyzers:
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_tags({"clean_mask": valve_pos_payload.clean_mask})
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_tags({"valve_mask": valve_pos_payload.valve_mask})
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_tags({"valve_pos": valve_pos_payload.valve_pos})
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_stopwatch_tag("valve_stable_time", valve_pos_payload.time)
            # The next line is for the simulator
            await self.farm.RPC[analyzer_rpc_name].DR_setValveMask(valve_pos_payload.valve_pos)

    async def set_mfc_setpoint(self, set_point):
        max_flow = self.farm.config.get_maximum_mfc_flow()
        if set_point > max_flow:
            set_point = max_flow
        await self.farm.RPC["MFC"].set_set_point(set_point)

    async def set_exhaust_valve(self, state):
        # Exhaust valve closes when it is energized
        await self.farm.RPC["Relay_0"].NUMATO_set_relay(0, state != "open")

    async def set_reference_valve(self, state):
        # Reference valve opens when it is energized
        await self.farm.RPC["Relay_0"].NUMATO_set_relay(1, state == "open")


async def main():
    pm = PigletManager()
    pm.start(1)
    event = Event(Signal.SYSTEM_CONFIGURE, SystemConfiguration(bank_list=[1, 3, 4]))
    Framework.publish(event)
    event = Event(Signal.PIGLET_REQUEST, PigletRequestPayload("*IDN?", [1, 3, 4]))
    Framework.publish(event)
    event = Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE standby", [1, 3, 4]))
    Framework.publish(event)
    event = Event(Signal.PIGLET_REQUEST, PigletRequestPayload("OPSTATE ident", [4]))
    Framework.publish(event)
    await asyncio.sleep(10)
    Framework.stop()


if __name__ == "__main__":
    # Uncomment these lines to get a visual execution trace
    # from async_hsm.SimpleSpy import SimpleSpy
    # Spy.enable_spy(SimpleSpy)
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
