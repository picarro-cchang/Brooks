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
from async_hsm.SimpleSpy import SimpleSpy
from experiments.state_machine.back_end.piglet_simulator import PigletSimulator
from experiments.state_machine.back_end.pigss_payloads import PigletRequestPayload, SystemConfiguration

POLL_PERIOD = 0.5


class PigletManager(Ahsm):
    def __init__(self):
        super().__init__()
        self.bank_list = None
        self.comm_lock = asyncio.Lock()
        self.piglets = {}
        self.tasks = []

    @state
    def _initial(self, e):
        self.piglet_status_te = TimeEvent("PIGLET_STATUS_TIMER")
        Framework.subscribe("PIGLET_REQUEST", self)
        Framework.subscribe("PIGLET_STATUS", self)
        Framework.subscribe("PIGLET_RESPONSE", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        Framework.subscribe("MFC_SET", self)
        Framework.subscribe("SIGTERM", self)
        return self.tran(self._configure)

    @state
    def _configure(self, e):
        sig = e.signal
        if sig == Signal.SYSTEM_CONFIGURE:
            payload = e.value
            self.bank_list = payload.bank_list
            return self.tran(self._manager)
        return self.super(self.top)

    @state
    def _manager(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.piglets = {bank: PigletSimulator(bank=bank) for bank in self.bank_list}
            self.piglet_status_te.postEvery(self, POLL_PERIOD)
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.piglet_status_te.disarm()
            for piglet in self.piglets.values():
                piglet.shutdown()
            return self.handled(e)
        elif sig == Signal.SIGTERM:
            return self.tran(self._exit)
        elif sig == Signal.PIGLET_REQUEST:
            payload = e.value
            print(f"Piglet request: {payload}")
            assert isinstance(payload, PigletRequestPayload)
            asyncio.create_task(self.send_to_piglets(payload.command, payload.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS_TIMER:
            asyncio.create_task(self.get_status(self.bank_list))
            return self.handled(e)
        elif sig == Signal.PIGLET_STATUS:
            print(f"Received PIGLET_STATUS, {e.value}; ", end="")
            piglet_status = e.value
            mfc_total = 0
            for bank in self.bank_list:
                mfc_total += piglet_status[bank]["MFC"]
            Framework.publish(Event(Signal.MFC_SET, {"time": piglet_status["time"], "mfc_setpoint": mfc_total}))
            return self.handled(e)
        elif sig == Signal.PIGLET_RESPONSE:
            print(f"Received PIGLET_RESPONSE, {e.value}")
            return self.handled(e)
        elif sig == Signal.MFC_SET:
            print(f"Setting MFC, {e.value}; ", end="")
            return self.handled(e)
        return self.super(self._configure)

    @state
    def _exit(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            for task in self.tasks:
                task.cancel()
            self.tasks = []
            return self.handled(e)
        return self.super(self.top)

    async def command_handler(self, command, bank):
        piglet = self.piglets[bank]
        return await piglet.cli(command)

    async def get_status_of_bank(self, bank):
        status = {}
        piglet = self.piglets[bank]
        status["STATE"] = await piglet.cli("OPSTATE?")
        status["MFC"] = float(await piglet.cli("MFC?"))
        status["SOLENOID_VALVES"] = int(await piglet.cli("CHANSET?"))
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
        response["time"] = time.time()
        Framework.publish(Event(Signal.PIGLET_STATUS, response))


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
