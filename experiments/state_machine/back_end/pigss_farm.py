#!/usr/bin/env python3
import asyncio
import attr
import traceback

from async_hsm import Spy, Event, Framework, Signal

from pigss_comms import PigssComms
from pigss_controller import PigssController
from piglet_manager import PigletManager


@attr.s
class PigssFarm:
    """Collection of Heirarchical State Machines for controlling PiGSS.
        The send_queue and receive_queue are used to transfer information
        to and from the UI via a web socket connection. These are passed
        to the controller, which runs the main HSM for interacting with
        the piglets. The comms state machine is used to communicate with
        the serial ports and to handle errors.
    """
    send_queue = attr.ib(factory=lambda: asyncio.Queue(maxsize=256))
    receive_queue = attr.ib(factory=lambda: asyncio.Queue(maxsize=256))
    # comms = attr.ib(factory=PigssComms)
    controller = attr.ib(factory=PigssController)
    piglet_manager = attr.ib(factory=PigletManager)
    tasks = attr.ib(factory=list)

    async def shutdown(self):
        await self.piglet_manager.shutdown()
        for task in self.tasks:
            task.cancel()
        Framework.publish(Event(Signal.TERMINATE, None))

    async def startup(self):
        try:
            self.controller.set_queues(self.send_queue, self.receive_queue)
            self.controller.set_piglet_manager(self.piglet_manager)
            from async_hsm.SimpleSpy import SimpleSpy
            # Spy.enable_spy(SimpleSpy)
            self.tasks.append(asyncio.create_task(self.controller.process_receive_queue_task()))
            self.controller.start(1)
            # self.comms.start(5)
            await self.piglet_manager.startup()
        except:
            print("Error starting up farm")
            print(traceback.format_exc())
            raise
