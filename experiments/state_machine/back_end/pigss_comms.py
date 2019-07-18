#!/usr/bin/env python3
import asyncio
from async_hsm import Ahsm, Event, Framework, Signal, Spy, run_forever, state, TimeEvent
from pigss_payloads import PcSendPayload, PcResponsePayload

class PigssComms(Ahsm):
    # State machine for communications with piglet
    # It waits for a PC_SEND signal with the message to send to the piglet
    #  (and an optional timeout) as its payload.
    # a) If the piglet replies within the specified time, it publishes
    #    the PC_RESPONSE signal with the message received from the piglet
    #    as its payload.
    # b) If the piglet responds with "-1" indicating a NAK, it publishes
    #    the PC_ERROR signal.
    # c) If the piglet does not respond, it publishes the PC_TIMEOUT signal
    #
    # It aslso responds to a PC_ABORT signal by stopping any pending timer
    #  and returning to the _ready_for_message state.

    def __init__(self):
        super().__init__()

    async def send_piglet(self, message):
        print(f"Sending to piglet: {message}")
        Framework.publish(Event(Signal._PC_RESPONSE, PcResponsePayload("world")))

    @state
    def _initial(self, e):
        self.message = None
        self.timeout = None
        Framework.subscribe("PC_ABORT", self)
        Framework.subscribe("PC_ERROR", self)
        Framework.subscribe("PC_RESPONSE", self)
        Framework.subscribe("PC_SEND", self)
        # Signal.register("PC_ERROR", self)
        # Signal.register("PC_RESPONSE", self)
        self.te = TimeEvent("PC_TIMEOUT")
        Framework.subscribe("TERMINATE", self)
        Framework.subscribe("_PC_RESPONSE", self)
        return self.tran(self._ready_for_message)

    @state
    def _ready_for_message(self, e):
        sig = e.signal
        if sig == Signal.PC_SEND:
            self.message = e.value.message
            self.timeout = e.value.timeout
            return self.tran(self._awaiting_response)
        elif sig == Signal.TERMINATE:
            print("Stopping framework")
            Framework.stop()
            return self.handled(e)
        elif sig == Signal.PC_RESPONSE:
            print(f"Sending PC_RESPONSE: {e.value.message}")
            return self.handled(e)
        return self.super(self.top)

    @state
    def _awaiting_response(self, e):
        sig = e.signal
        if sig == Signal.ENTRY:
            self.te.postIn(self, self.timeout)  # Post a timeout unless response arrives first
            asyncio.ensure_future(self.send_piglet(self.message))
            return self.handled(e)
        elif sig == Signal.EXIT:
            self.te.disarm()
            return self.handled(e)
        elif sig == Signal.PC_ABORT:
            return self.tran(self._ready_for_message)
        elif sig == Signal._PC_RESPONSE:
            # We have received a response from the piglet, placed in e.value.message
            if e.value.message.strip() == "-1":
                # The response -1 is a NAK from the piglet
                Framework.publish(Event(Signal.PC_ERROR, None))
            else:
                # This is a good response, so publish it in payload of a PC_RESPONSE
                Framework.publish(Event(Signal.PC_RESPONSE, PcResponsePayload(e.value.message)))
            return self.tran(self._ready_for_message)
        return self.super(self._ready_for_message)

if __name__ == "__main__":
    # Uncomment this line to get a visual execution trace (to demonstrate debugging)
    from async_hsm.SimpleSpy import SimpleSpy
    Spy.enable_spy(SimpleSpy)

    pc = PigssComms()
    pc.start(2)

    e = Event(Signal.PC_SEND, PcSendPayload("Hello", 1.0))
    Framework.publish(e)

    run_forever()
