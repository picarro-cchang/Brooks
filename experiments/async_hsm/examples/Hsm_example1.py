import asyncio
from async_hsm import Ahsm, Event, Framework, Signal, Spy, state
from async_hsm.SimpleSpy import SimpleSpy
import signal


class HsmExample1(Ahsm):
    @state
    def _initial(self, e):
        Signal.register("E1")
        Signal.register("E2")
        return self.tran(self.state1)

    @state
    def state1(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            print("ENTRY action 1")
            return self.handled(e)
        elif sig == Signal.EXIT:
            print("EXIT action 1")
            return self.handled(e)
        elif sig == Signal.INIT:
            print("INIT action 1")
            return self.tran(self.state2)
        elif sig == Signal.E1:
            print("Event 1 action 1")
            return self.handled(e)
        elif sig == Signal.E2:
            print("Event 2 action 1")
            return self.tran(self.state1)
        return self.super(self.top)

    @state
    def state2(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            print("ENTRY action 2")
            return self.handled(e)
        elif sig == Signal.EXIT:
            print("EXIT action 2")
            return self.handled(e)
        elif sig == Signal.E1:
            print("Event 1 action 2")
            1 / 0
            return self.tran(self.state1)
        elif sig == Signal.E2:
            print("Event 2 action 2")
            return self.tran(self.state3)
        return self.super(self.state1)

    @state
    def state3(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            print("ENTRY action 3")
            return self.handled(e)
        elif sig == Signal.EXIT:
            print("EXIT action 3")
            return self.handled(e)
        return self.super(self.state1)


async def main():
    hsm = HsmExample1()
    # Spy.enable_spy(SimpleSpy)
    # SimpleSpy.on_framework_add(hsm)
    seq = ['E1', 'E2', 'E1', 'E2']
    hsm.start(0)
    while not hsm.terminated:
        if seq:
            sig_name = seq.pop(0)
            print(f'\tEvent --> {sig_name}')
        else:
            sig_name = input('\tEvent --> ')
        try:
            sig = getattr(Signal, sig_name)
            hsm.postFIFO(Event(sig, None))
        except LookupError:
            print("\nInvalid signal name", end="")
            continue
        while hsm.has_msgs():
            event = hsm.pop_msg()
            hsm.dispatch(event)
    print("\nTerminated")
    await Framework.done()


if __name__ == "__main__":
    asyncio.run(main())
