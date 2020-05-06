"""
The piglet manager provides an interface to a number of piglets (or piglet simulators)
and gathers status information from them periodically.

The piglet objects are stored in a dictionary, keyed by the bank number (1-origin)

The run() coroutine starts up the finite state machines within the piglet simulators as well
    as a scheduler which runs the get_status coroutines, one for each piglet. These get_status
    coroutines are called at the multiples of POLL_PERIOD, as measured by the time.monotonic
    clock.

Calls to get_status() for each piglet make a dictionary which is populated via calls to the
    command line interface of the piglet. In the actual hardware, this will involve serial
    communications. After status is collected from all the piglets, we can aggregate the MFC
    setpoint requests and send the sum to the MFC (not yet implemented).

An additional coroutine command_handler(bank, command) allows for direct communications with
    the individual piglets. These accesses have to be interleaved with the status gathering,
    and this is achieved by using a mutex lock (self.comm_lock) which ensures that 
    accessing the piglet CLIs do not interfere with each other. Note that the lock is held
    by the staus collection routine until the status from all piglets have been collected. 
    This will hopefully mean that the all of these status requests occur close to each other 
    in time.

An Event of type PIGLET_STATUS is published whenever status has been collected from all the 
    piglets. It contains a JSON payload with a timestamp (normal epoch time, not the monotonic) 
    and all the status information collected.
    
"""
import asyncio
import json
import math
import time

import attr

from async_hsm import Event, Framework, Signal
from piglet_simulator import PigletSimulator

NUM_PIGLETS = 4
POLL_PERIOD = 0.5

@attr.s
class PigletManager:
    piglets = attr.ib(factory=lambda: {i+1: PigletSimulator(bank=i+1) for i in range(NUM_PIGLETS)})
    comm_lock = attr.ib(factory=lambda: asyncio.Lock())
    tasks = attr.ib(factory=list)

    async def send_to_one_piglet(self, bank, command):
        result = await self.command_handler(bank, command)
        Framework.publish(Event(Signal.PIGLET_RESPONSE, result))
        return result

    async def send_to_all_piglets(self, command):
        result = {}
        for bank in self.piglets:
            result[bank] = await self.command_handler(bank, command)
        Framework.publish(Event(Signal.PIGLET_RESPONSE, result))
        return result

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()

    async def startup(self):
        Signal.register("PIGLET_STATUS")
        Signal.register("PIGLET_RESPONSE")
        self.tasks.append(asyncio.create_task(self.scheduler(POLL_PERIOD)))
        for piglet in self.piglets.values():
            self.tasks.append(asyncio.create_task(piglet.fsm()))

        # await asyncio.gather(self.scheduler(POLL_PERIOD), *[piglet.fsm() for piglet in self.piglets.values()])

    async def command_handler(self, bank, command):
        async with self.comm_lock:
            piglet = self.piglets[bank]
            return await piglet.cli(command)

    async def scheduler(self, period):
        when = 0
        while True:
            now = time.monotonic()
            when = max(when + period, period * math.ceil(now / period))
            if when > now:
                await asyncio.sleep(when - now)
            actual = time.time()
            async with self.comm_lock:
                result = await asyncio.gather(*[self.get_status(i+1) for i in range(NUM_PIGLETS)])
            msg = {"time": actual, "status": result}
            Framework.publish(Event(Signal.PIGLET_STATUS, json.dumps(msg)))
            print(f"Completed get_status for all piglets at {actual}, {result}")

    async def get_status(self, bank):
        status = {}
        piglet = self.piglets[bank]
        status["STATE"] = await piglet.cli("OPSTATE?")
        status["MFC"] = float(await piglet.cli("MFC?"))
        status["SOLENOID_VALVES"] = int(await piglet.cli("CHANSET?"))
        return status


async def main():
    pm = PigletManager()
    await pm.run()


if __name__ == "__main__":
    asyncio.run(main())
