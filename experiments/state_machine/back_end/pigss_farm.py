#!/usr/bin/env python3
import asyncio
import traceback

import attr

from experiments.LOLogger.LOLoggerClient import LOLoggerClient
from experiments.state_machine.back_end.piglet_manager import PigletManager
from experiments.state_machine.back_end.pigss_controller import PigssController
from experiments.state_machine.back_end.pigss_supervisor import PigssSupervisor

log = LOLoggerClient(client_name="PigssFarm", verbose=True)


@attr.s
class PigssFarm:
    """Collection of Heirarchical State Machines for controlling PiGSS.
        The send_queue and receive_queue are used to transfer information
        to and from the UI via a web socket connection. These are passed
        to the controller, which runs the main HSM for interacting with
        the piglets. The comms state machine is used to communicate with
        the serial ports and to handle errors.
    """
    simulation = attr.ib(default=False)
    send_queue = attr.ib(factory=lambda: asyncio.Queue(maxsize=256))
    receive_queue = attr.ib(factory=lambda: asyncio.Queue(maxsize=256))
    tasks = attr.ib(factory=list)
    RPC = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        self.controller = PigssController(self, simulation=self.simulation)
        self.piglet_manager = PigletManager(self, simulation=self.simulation)
        self.pigss_supervisor = PigssSupervisor(self, simulation=self.simulation)

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()
        # Framework.publish(Event(Signal.TERMINATE, None))

    async def startup(self):
        try:
            log.info(f"Starting up farm of state machines")
            self.controller.set_queues(self.send_queue, self.receive_queue)
            # from async_hsm.SimpleSpy import SimpleSpy
            # Spy.enable_spy(SimpleSpy)
            self.tasks.append(asyncio.create_task(self.controller.process_receive_queue_task()))
            self.piglet_manager.start(3)
            self.controller.start(2)
            self.pigss_supervisor.start(1)
        except Exception:
            log.error(f"Error setting up farm\n{traceback.format_exc()}")
            raise
