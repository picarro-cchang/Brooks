"""
The piglet manager provides an interface to a number of piglets (or piglet simulators)
and gathers status information from them periodically.

The piglet objects are stored in a dictionary, keyed by the bank number (1-origin)

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
import asyncio
import time

from async_hsm import Ahsm, Event, Framework, Signal, Spy, TimeEvent, state
# from async_hsm.SimpleSpy import SimpleSpy
from experiments.state_machine.back_end.pigss_payloads import (PigletRequestPayload, SystemConfiguration, ValvePositionPayload)

POLL_PERIOD = 0.5


class PigletManager(Ahsm):
    def __init__(self, farm):
        super().__init__()
        self.farm = farm
        self.bank_list = None
        self.mad_mapper_result = None
        self.picarro_analyzers = []
        self.comm_lock = asyncio.Lock()
        self.valve_mask = 0
        self.clean_mask = 0
        self.tasks = []
        self.piglet_fp = open("/tmp/piglets", "w")

    @state
    def _initial(self, e):
        self.publish_errors = True
        self.piglet_status_te = TimeEvent("PIGLET_STATUS_TIMER")
        Framework.subscribe("MFC_SET", self)
        Framework.subscribe("PIGLET_REQUEST", self)
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("SET_EXHAUST_VALVE", self)
        Framework.subscribe("SET_REFERENCE", self)
        Framework.subscribe("SET_REFERENCE_VALVE", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("VALVE_POSITION", self)
        Framework.subscribe("TERMINATE", self)
        self.exhaust_open = False
        self.reference_open = False
        self.pending = False
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
            self.run_async(self.set_reference(0))
            self.piglet_status_te.postEvery(self, POLL_PERIOD)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.piglet_status_te.disarm()
            return self.handled(e)
        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)
        elif sig == Signal.SET_REFERENCE:
            payload = e.value
            Framework.publish(Event(Signal.SET_REFERENCE_VALVE, {"time": time.time(), "value": "open" if payload else "close"}))
            self.reference_open = (payload != 0)
            self.run_async(self.set_reference(payload))
            return self.handled(e)
        elif sig == Signal.SET_REFERENCE_VALVE:
            print(f'Reference value set: {e.value}', file=self.piglet_fp, flush=True)
            return self.handled(e)
        elif sig == Signal.PIGLET_REQUEST:
            payload = e.value
            assert isinstance(payload, PigletRequestPayload)
            self.run_async(self.send_to_piglets(payload.command, payload.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS_TIMER:
            self.run_async(self.get_status(self.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS:
            #for bank in self.bank_list:
            #    print(f'{bank} {e.value[bank]["OPSTATE"]} {e.value[bank]["IDSTATE"]} {e.value[bank]["MFCVAL"]}', file=self.piglet_fp, flush=True)
            print(file=self.piglet_fp)
            piglet_status = e.value
            mfc_total = 0
            for bank in self.bank_list:
                mfc_total += piglet_status[bank]["MFCVAL"]
            if self.reference_open:
                mfc_total = self.farm.config.get_reference_mfc_flow()
            if mfc_total == 0:
                if not self.exhaust_open and not self.pending:
                    self.pending = True
                    self.run_async(self.open_exhaust_then_set_mfc(mfc_total, delay=self.farm.config.get_flow_settle_delay()))
                else:
                    Framework.publish(Event(Signal.MFC_SET, {"time": e.value["time"], "mfc_setpoint": mfc_total}))
            elif mfc_total > 0:
                if self.exhaust_open and not self.pending:
                    self.pending = True
                    self.run_async(self.set_mfc_then_close_exhaust(mfc_total, delay=self.farm.config.get_flow_settle_delay()))
                else:
                    Framework.publish(Event(Signal.MFC_SET, {"time": e.value["time"], "mfc_setpoint": mfc_total}))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            # print(f"Received PIGLET_RESPONSE, {e.value}")
            return self.handled(e)
        elif sig == Signal.MFC_SET:
            print(f"MFC setting: {e.value}", file=self.piglet_fp, flush=True)
            return self.handled(e)
        elif sig == Signal.SET_EXHAUST_VALVE:
            print(f"Exhaust valve: {e.value}", file=self.piglet_fp, flush=True)
            return self.handled(e)
        elif sig == Signal.VALVE_POSITION:
            print(f"\n\nReceived VALVE_POSITION: {e.value}\n")
            self.run_async(self.handle_valve_position(e.value))
            return self.handled(e)
        return self.super(self._configure)

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

    async def open_exhaust_then_set_mfc(self, mfc_total, delay):
        Framework.publish(Event(Signal.SET_EXHAUST_VALVE, {"time": time.time(), "value": "open"}))
        self.exhaust_open = True
        await asyncio.sleep(delay)
        Framework.publish(Event(Signal.MFC_SET, {"time": time.time(), "mfc_setpoint": mfc_total}))
        await asyncio.sleep(delay)
        self.pending = False

    async def set_mfc_then_close_exhaust(self, mfc_total, delay):
        Framework.publish(Event(Signal.MFC_SET, {"time": time.time(), "mfc_setpoint": mfc_total}))
        await asyncio.sleep(delay)
        Framework.publish(Event(Signal.SET_EXHAUST_VALVE, {"time": time.time(), "value": "close"}))
        self.exhaust_open = False
        await asyncio.sleep(delay)
        self.pending = False

    async def command_handler(self, command, bank):
        # piglet = self.piglets[bank]
        # return await piglet.cli(command)
        return await self.farm.RPC[f"Piglet_{bank}"].send(command)

    async def get_status_of_bank(self, bank):
        status = {}
        # piglet = self.piglets[bank]
        # status["OPSTATE"] = await piglet.cli("OPSTATE?")
        # status["MFCVAL"] = float(await piglet.cli("MFCVAL?"))
        # status["SOLENOID_VALVES"] = int(await piglet.cli("CHANSET?"))
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
        try:
            response = await self.exec_on_banks(lambda bank: self.command_handler(command, bank), bank_list)
            Framework.publish(Event(Signal.PIGLET_RESPONSE, response))
        except Exception:
            raise
            # print("Send to piglets failed!")

    async def get_status(self, bank_list):
        try:
            response = await self.exec_on_banks(self.get_status_of_bank, bank_list)
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
                Framework.publish(
                    Event(Signal.VALVE_POSITION, ValvePositionPayload(now, valve_pos, self.valve_mask, self.clean_mask)))
            response["time"] = now
            Framework.publish(Event(Signal.PIGLET_STATUS, response))
        except Exception:
            raise
            # print("Get piglet status failed!")

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

    async def set_reference(self, reference_active):
        for analyzer_rpc_name in self.picarro_analyzers:
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_tags({"reference": reference_active})
            await self.farm.RPC[analyzer_rpc_name].IDRIVER_add_stopwatch_tag("valve_stable_time")


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
    # Uncomment this line to get a visual execution trace (to demonstrate debugging)
    # Spy.enable_spy(SimpleSpy)
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
