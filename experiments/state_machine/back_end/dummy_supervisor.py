import asyncio
import json
import os
import time

from async_hsm import Ahsm, Event, Framework, Signal, Spy, TimeEvent, state
from async_hsm.SimpleSpy import SimpleSpy
from experiments.state_machine.back_end.piglet_simulator import PigletSimulator
from experiments.state_machine.back_end.pigss_payloads import PigletRequestPayload, SystemConfiguration
from experiments.common.async_helper import log_async_exception

my_path = os.path.dirname(os.path.abspath(__file__))


class DummySupervisor(Ahsm):
    def __init__(self):
        super().__init__()

    @state
    def _initial(self, e):
        Framework.subscribe("MADMAPPER_DONE", self)
        Framework.subscribe("SYSTEM_CONFIGURE", self)
        return self.tran(self._mapping)

    @state
    def _mapping(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            asyncio.create_task(self.dummy_mapper())
            return self.handled(e)
        elif sig == Signal.MADMAPPER_DONE:
            payload = e.value
            bank_list = []
            for name, descr in payload["Devices"]["Serial_Devices"].items():
                if descr["Driver"] == "PigletDriver":
                    bank_list.append(descr["Bank_ID"])
            Framework.publish(
                Event(Signal.SYSTEM_CONFIGURE, SystemConfiguration(bank_list=sorted(bank_list), mad_mapper_result=payload)))
            return self.tran(self._supervising)
        return self.super(self.top)

    @state
    def _supervising(self, e):
        sig = e.signal
        if sig == Signal.SYSTEM_CONFIGURE:
            print(f"System config: {e.value}")
            return self.handled(e)
        return self.super(self.top)

    @log_async_exception(stop_loop=True)
    async def dummy_mapper(self):
        with open(os.path.join(my_path, "madmapper.json"), "r") as fp:
            mapper_dict = json.load(fp)
            await asyncio.sleep(3.0)
            Framework.publish(Event(Signal.MADMAPPER_DONE, mapper_dict))


async def main():
    ds = DummySupervisor()
    ds.start(1)
    await asyncio.sleep(10)
    Framework.stop()


if __name__ == "__main__":
    # Uncomment this line to get a visual execution trace (to demonstrate debugging)
    Spy.enable_spy(SimpleSpy)
    asyncio.ensure_future(main())
    asyncio.get_event_loop().run_forever()
