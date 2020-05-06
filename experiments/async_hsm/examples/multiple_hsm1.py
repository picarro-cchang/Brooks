#!/usr/bin/env python3
import asyncio
import traceback

from async_hsm import Ahsm, Event, Framework, Signal, Spy, TimeEvent, state


class MyHsm(Ahsm):
    def __init__(self, parent, name, period):
        super().__init__()
        self.parent = parent
        self.name = name
        self.period = period

    @state
    def _initial(self, e):
        Framework.subscribe("TERMINATE", self)
        self.te = TimeEvent(f"TIMER_{self.name}")
        print(self.te)
        return self.tran(self._running)

    @state
    def _running(self, event):
        sig = event.signal
        if sig == Signal.ENTRY:
            print(f"{self.name} enters running state, period {self.period}")
            self.te.postEvery(self, self.period)
            return self.handled(event)

        elif sig == getattr(Signal, f"TIMER_{self.name}"):
            print(f"{self.name} receives tick")
            return self.handled(event)

        elif sig == Signal.EXIT:
            self.te.disarm()
            return self.handled(event)

        elif sig == Signal.TERMINATE:
            return self.tran(self._exit)

        return self.super(self.top)

    @state
    def _exit(self, event):
        sig = event.signal
        if sig == Signal.ENTRY:
            print(f"{self.name} terminating")
            return self.handled(event)
        return self.super(self.top)


class MultipleHsm:
    """
    Start a collection of HSMs running in a single asyncio event loop.
    We wish to investigate exception handling and error recovery so that
    the HSM in which an exception occurs is identified and so that an
    error in one does not cause all machines to be killed
    """
    def __init__(self):
        self.hsm1 = MyHsm(self, 'alpha', 3)
        self.hsm2 = MyHsm(self, 'beta', 2)
        self.tasks = []

    async def shutdown(self):
        print(f"Calling shutdown in MultipleHsm")
        for task in self.tasks:
            task.cancel()

    async def startup(self):
        try:
            print(f"Starting up multiple state machines")
            self.hsm1.start(1)
            self.hsm2.start(2)
        except Exception:
            print(f"Error setting up state machines\n{traceback.format_exc()}")
            raise


def main():
    try:
        multi = MultipleHsm()
        loop = asyncio.get_event_loop()
        loop.create_task(multi.startup())
        loop.run_forever()
    except Exception:
        print(f"\nCaught exception in main\n{traceback.format_exc()}")
    finally:
        try:
            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()


if __name__ == "__main__":
    main()
