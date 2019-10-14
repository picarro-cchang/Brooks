import asyncio
import collections
import signal
import traceback
import typing
from copy import copy
from functools import wraps

import attr


@attr.s(auto_attribs=True)
class Catch:
    signal: str
    handler: str


@attr.s(auto_attribs=True)
class State:
    name: str
    parent: typing.Optional[str]
    catches: typing.List[Catch] = attr.Factory(list)


@attr.s(auto_attribs=True)
class HsmDescription:
    initial: str
    setup: typing.Optional[str]
    signals: typing.List[str] = attr.Factory(list)
    states: typing.List[State] = attr.Factory(list)


class Spy(object):
    """Spy is the debugging system for async_hsm.
    async_hsm contains a handful of Spy.on_*() methods
    placed at useful locations in the framework.
    It is up to a Spy driver (such as the included VcdSpy)
    to implement the Spy.on_*() methods.
    The programmer calls Spy.enable_spy(<Spy implementation class>)
    to activate the Spy system; otherwise, Spy does nothing.
    Therefore, this class is designed so that calling Spy.anything()
    is inert unless the application first calls Spy.enable_spy()
    """
    _actv_cls = None

    @staticmethod
    def enable_spy(spy_cls):
        """Sets the Spy to use the given class
        and calls its initializer.
        """
        Spy._actv_cls = spy_cls
        spy_cls.init()

    def __getattr__(*args):
        """Returns
        1) the enable_spy static method if requested by name, or
        2) the attribute from the active class (if active class was set), or
        3) a function that swallows any arguments and does nothing.
        """
        if args[1] == "enable_spy":
            return Spy.enable_spy
        if Spy._actv_cls:
            return getattr(Spy._actv_cls, args[1])
        return lambda *x: None


# Singleton pattern:
# Turn Spy into an instance of itself so __getattribute__ works
# on anyone who calls "import Spy; Spy.foo()"
# This  prevents Spy() from creating a new instance
# and gives everyone who calls "import Spy" the same object
Spy = Spy()


class Signal(object):
    """An asynchronous stimulus that triggers reactions.
    A unique identifier that, along with a value, specifies an Event.
    p. 154
    """

    _registry = {}  # signame:str to sigid:int
    _lookup = []  # sigid:int to signame:str

    @staticmethod
    def exists(signame):
        """Returns True if signame is in the Signal registry.
        """
        return signame in Signal._registry

    @staticmethod
    def register(signame):
        """Registers the signame if it is not already registered.
        Returns the signal number for the signame.
        """
        assert type(signame) is str
        if signame in Signal._registry:
            # TODO: emit warning that signal is already registered
            return Signal._registry[signame]
        else:
            sigid = len(Signal._lookup)
            Signal._registry[signame] = sigid
            Signal._lookup.append(signame)
            Spy.on_signal_register(signame, sigid)
            return sigid

    def __getattr__(self, signame):
        assert type(signame) is str
        return Signal._registry[signame]


# Singleton pattern:
# Turn Signal into an instance of itself so getattr works.
# This also prevents Signal() from creating a new instance.
Signal = Signal()

# Register the reserved (system) signals
Signal.register("EMPTY")  # 0
Signal.register("ENTRY")  # 1
Signal.register("EXIT")  # 2
Signal.register("INIT")  # 3
Signal.register("TERMINATE")  # 4
Signal.register("ERROR")  # 5

Event = collections.namedtuple("Event", ["signal", "value"])

Event.__doc__ = """Events are a tuple of (signal, value) that are passed from
    one AHSM to another.  Signals are defined in each AHSM's source code
    by name, but resolve to a unique number.  Values are any python value,
    including containers that contain even more values.  Each AHSM state
    (static method) accepts an Event as the parameter and handles the event
    based on its Signal."""

# Instantiate the reserved (system) events
Event.EMPTY = Event(Signal.EMPTY, None)
Event.ENTRY = Event(Signal.ENTRY, None)
Event.EXIT = Event(Signal.EXIT, None)
Event.INIT = Event(Signal.INIT, None)
Event.TERMINATE = Event(Signal.TERMINATE, None)
Event.ERROR = Event(Signal.ERROR, None)

# The order of this tuple MUST match their respective signals
Event.reserved = (Event.EMPTY, Event.ENTRY, Event.EXIT, Event.INIT, Event.TERMINATE, Event.ERROR)


def state(func):
    """A decorator that identifies which methods are states.
    The presence of the async_hsm_state attr, not the value of the attr,
    determines statehood.
    The Spy debugging system uses the async_hsm_state attribute
    to determine which methods inside a class are actually states.
    Other uses of the attribute may come in the future.
    """
    @wraps(func)
    def func_wrap(self, evt):
        result = func(self, evt)
        Spy.on_state_handler_called(func_wrap, evt, result)
        return result

    setattr(func_wrap, "async_hsm_state", True)
    return func_wrap


class Hsm(object):
    """A Hierarchical State Machine (HSM).
    Full support for hierarchical state nesting.
    Guaranteed entry/exit action execution on arbitrary state transitions.
    Full support of nested initial transitions.
    Support for events with arbitrary parameters.
    """

    # Every state handler must return one of these values
    RET_HANDLED = 0
    RET_IGNORED = 1
    RET_TRAN = 2
    RET_SUPER = 3

    def __init__(self):
        """Sets this Hsm's current state to self.top(), the default state
        and stores the given initial state.
        """
        # self.state is the Hsm/act's current active state.
        # This instance variable references the message handler (method)
        # that will be called whenever a message is sent to this Hsm.
        # We initialize this to self.top, the default message handler
        self.state = self.top
        self.state_receiving_dispatch = None
        # The terminated flag indicates that this state machine is
        #  finished. Usually set in the _exit state.
        self.terminated = False
        #
        # The publish_errors flag affects how exceptions raised in this
        #  HSM are treated. The resulting Event with type Signal.ERROR
        #  may be published to the framework (if publish_errors is True)
        #  or placed on the FIFO of this Hsm (if publish_errors is False)
        # If the error is publised, it is necessary to use the subscribe
        #  method to be informed when the error occurs.
        self.publish_errors = False
        # Async_hsm differs from QP here in that we hardcode
        # the initial state to be "_initial"

    def _initial(self, event):
        """Raises a NotImplementedError to force the derived class
        to implement its own initial state.
        """
        raise NotImplementedError

    @state
    def _exit(self, event):
        """Default exit state handler that sets the terminated attribute of the
            state machine. This may be overridden in a user's HSM class. """
        sig = event.signal
        if sig == Signal.ENTRY:
            self.terminated = True
            return self.handled(event)
        return self.super(self.top)

    # Helper functions to process reserved events through the current state
    def trig(self, state_func, signal):
        return state_func(Event.reserved[signal])

    def enter(self, state_func):
        return state_func(Event.ENTRY)

    def exit(self, state_func):
        return state_func(Event.EXIT)

    # Other helper functions
    def handled(self, event):
        return Hsm.RET_HANDLED

    def tran(self, nextState):
        self.state = getattr(self, nextState) if isinstance(nextState, str) else nextState
        return Hsm.RET_TRAN

    def super(self, superState):
        if superState is None:
            self.state = self.top
        else:
            self.state = getattr(self, superState) if isinstance(superState, str) else superState
        return Hsm.RET_SUPER  # p. 158

    def run_async(self, cor):
        # Run an asynchronous task in the coroutine cor and post an ERROR
        #  event if it throws an exception
        async def wrapped_cor():
            try:
                await cor
            except Exception as e:
                event = Event(Signal.ERROR, {
                    "exc": e,
                    "traceback": traceback.format_exc(),
                    "location": self.__class__.__name__,
                    "name": cor.__name__
                })
                if self.publish_errors:
                    Framework.publish(event)
                else:
                    self.postFIFO(event)

        return asyncio.ensure_future(wrapped_cor())

    def top(self, event):
        """This is the default state handler. This handler ignores all signals except for Signal.TERMINATE and
        Signal.ERROR. These default actions can be overridden within a user-provided top level state.

        The TERMINATE signal causes a transition to the state self._exit.
        The ERROR signal does not cause a state transition, but prints a tracback message on the console.
        """
        if event.signal == Signal.TERMINATE:
            return self.tran(self._exit)
        elif event.signal == Signal.ERROR:
            print(f"Exception {event.value['exc']}\n{event.value['traceback']}")
            return Hsm.RET_HANDLED
        # All other events are quietly ignored
        return Hsm.RET_IGNORED  # p. 165

    def _perform_init_chain(self, current):
        """Act on the chain of initializations required starting from current."""
        t = current
        while self.trig(t if t != self.top else self._initial, Signal.INIT) == Hsm.RET_TRAN:
            # The state handles the INIT message and needs to make a transition. The
            #  "top" state is special in that it does not handle INIT messages, so we
            #  defer to self._initial in this case
            path = []  # Trace the path back to t via superstates
            while self.state != t:
                path.append(self.state)
                self.trig(self.state, Signal.EMPTY)
            # Restore the state to the target state
            self.state = path[0]
            assert len(path) < 32  # MAX_NEST_DEPTH
            # Perform ENTRY action for each state from current to the target
            path.reverse()  # in-place
            for s in path:
                self.enter(s)
            # The target state has now to be checked to see if it responds to the INIT message
            t = path[-1]  # -1 because path was reversed
        return t

    def _perform_transition(self, source, target):
        # Handle the state transition from source to target in the HSM.
        s, t = source, target
        path = [t]
        if s == t:  # Case (a), transition to self
            self.exit(s)
            self.enter(t)
        else:
            # Find parent of target
            self.trig(t, Signal.EMPTY)
            t = self.state  # t is now parent of target
            if s == t:  # Case (b), source is parent of target
                self.enter(path[0])
            else:
                # Find parent of source
                self.trig(s, Signal.EMPTY)
                if self.state == t:  # Case (c), source and target share a parent
                    self.exit(s)
                    self.enter(path[0])
                else:
                    if self.state == path[0]:  # Case (d), target is parent of source
                        self.exit(s)
                    else:  # Check if the source is an ancestor of the target (case (e))
                        lca_found = False
                        path.append(t)  # Populates path[1]
                        t = self.state  # t is now parent of source
                        # Find and save ancestors of target into path
                        #  until we find the source or hit the top
                        self.state = path[1]
                        while self.state != self.top:
                            self.trig(self.state, Signal.EMPTY)
                            path.append(self.state)
                            assert len(path) < 32  # MAX_NEST_DEPTH
                            if self.state == s:
                                lca_found = True
                                break
                        if lca_found:  # This is case (e), enter states to get to target
                            for st in reversed(path[:-1]):
                                self.enter(st)
                        else:
                            self.exit(s)  # Exit the source for cases (f), (g), (h)
                            self.state = t  # Start at parent of the source
                            while self.state not in path:
                                # Keep exiting up into superstates until we reach the LCA.
                                #  Depending on whether the EXIT signal is handled, we may also need
                                #  to send the EMPTY signal to make self.state climb to the superstate.
                                if self.exit(self.state) == Hsm.RET_HANDLED:
                                    self.trig(self.state, Signal.EMPTY)
                            t = self.state
                            # Step into children until we enter the target
                            for st in reversed(path[:path.index(t)]):
                                self.enter(st)

    def init(self):
        """Transitions to the initial state.  Follows any INIT transitions
        from the inital state and performs ENTRY actions as it proceeds.
        Use this to pass any parameters to initialize the state machine.
        p. 172
        """
        # The initial state MUST transition to another state
        self.state = self._perform_init_chain(self.top)

    def dispatch(self, event):
        """Dispatches the given event to this Hsm.
        Follows the application's state transitions
        until the event is handled or top() is reached
        p. 174
        """
        try:
            Spy.on_hsm_dispatch_event(event)

            # Save the current state
            t = self.state
            self.state_receiving_dispatch = t

            # Proceed to superstates if event is not handled, we wish to find the superstate
            #  (if any) that does handle the event and to record the path to that state
            exit_path = []
            r = Hsm.RET_SUPER
            while r == Hsm.RET_SUPER:
                s = self.state
                exit_path.append(s)
                Spy.on_hsm_dispatch_pre(s)
                r = s(event)  # invoke state handler
            # We leave the while loop with s at the state which was able to respond
            #  to the event, or to self.top if none did
            Spy.on_hsm_dispatch_post(exit_path)

            # If the state handler for s requests a transition
            if r == Hsm.RET_TRAN:
                t = self.state
                # Store target of transition
                # Exit from the current state to the state s which handles
                # the transition. We do not exit from s=exit_path[-1] itself.
                for st in exit_path[:-1]:
                    r = self.exit(st)
                    assert (r == Hsm.RET_SUPER) or (r == Hsm.RET_HANDLED)
                s = exit_path[-1]
                # Transition to t through the HSM
                self._perform_transition(s, t)
                # Do initializations starting at t
                t = self._perform_init_chain(t)

            # Restore the state
            self.state = t
            self.state_receiving_dispatch = None

        except Exception as e:
            event = Event(Signal.ERROR, {"exc": e, "traceback": traceback.format_exc(), "location": self.__class__.__name__})
            if self.publish_errors:
                Framework.publish(event)
            else:
                self.postFIFO(event)


class Framework(object):
    """Framework is a composite class that holds:
    - the asyncio event loop
    - the registry of AHSMs
    - the set of TimeEvents
    - the handle to the next TimeEvent
    - the table subscriptions to events
    """

    # The event loop is accessed through the get_event_loop method. The private
    #  attribute __event_loop is initialized the first time get_event_loop is called
    #  and is subsequently returned by the get_event_loop method
    __event_loop = None

    # The Framework maintains a registry of Ahsms in a list.
    _ahsm_registry = []

    # The Framework maintains a dict of priorities in use
    # to prevent duplicates.
    # An Ahsm's priority is checked against this dict
    # within the Ahsm.start() method
    # when the Ahsm is added to the Framework.
    # The dict's key is the priority (integer) and the value is the Ahsm.
    _priority_dict = {}

    # The Framework maintains pending TimeEvents in a dict.
    #  The TimeEvent is the key and the handle to the callback
    #  is the value. This is useful for cancelling the event if
    #  necessary. A time event can appear at most once within
    #  this dictionary, since it cannot be scheduled while it ia
    #
    #  A nonperiodic time event will be removed from
    #  the dictionary when it expires, whereas periodic TimeEvents
    #  re-enqueue themselves and update their handles whenever
    #  they occur.
    _time_event_handles = {}

    # The Subscriber Table is a dictionary.  The keys are signals.
    # The value for each key is a list of Ahsms that are subscribed to the
    # signal.  An Ahsm may subscribe to a signal at any time during runtime.
    _subscriber_table = {}

    # The terminate event is accessed through the get_terminate_event method. The private
    #  attribute __terminate_event is initialized the first time get_terminate_event is called
    #  and is subsequently returned by the get_terminate_event method
    # The event is set once all the AHSMs in the framework have set their terminated attribute,
    #  which is usually done in their _exit states
    __terminate_event = None

    @staticmethod
    def get_event_loop():
        # The first time this is called, we get the current event loop and assign it to the
        #  private variable __event_loop. Subsequently, return this loop. Doing this allows us
        #  use asyncio.run in conjunction with async_hsm, since asyncio.run creates a new
        #  event loop, and needs to be run before we try to call get_event_loop
        if Framework.__event_loop is None:
            Framework.__event_loop = asyncio.get_event_loop()
            # try:
            #     Framework.__event_loop.add_signal_handler(signal.SIGINT, lambda: Framework.stop())
            #     Framework.__event_loop.add_signal_handler(signal.SIGTERM, lambda: Framework.stop())
            #     Framework.__event_loop.add_signal_handler(29, Framework.print_info)
            # except NotImplementedError:
            #     pass
        return Framework.__event_loop

    @staticmethod
    def get_terminate_event():
        # The first time this is called, we get the current event loop and assign it to the
        #  private variable __event_loop. Subsequently, return this loop. Doing this allows us
        #  use asyncio.run in conjunction with async_hsm, since asyncio.run creates a new
        #  event loop, and needs to be run before we try to call get_event_loop
        if Framework.__terminate_event is None:
            Framework.__terminate_event = asyncio.Event()
        return Framework.__terminate_event

    @staticmethod
    def post(event, act):
        """Posts the event to the given Ahsm's event queue.
        The argument, act, is an Ahsm instance.
        """
        assert isinstance(act, Ahsm)
        act.postFIFO(event)

    @staticmethod
    def post_by_name(event, act_name):
        """Posts the event to the given Ahsm's event queue.
        The argument, act, is a string of the name of the class
        to which the event is sent.  The event will post to all actors
        having the given classname.
        """
        assert type(act_name) is str
        for act in Framework._ahsm_registry:
            if act.__class__.__name__ == act_name:
                act.postFIFO(event)

    @staticmethod
    def publish(event):
        """Posts the event to the message queue of every Ahsm
        that is subscribed to the event's signal.
        """
        if event.signal in Framework._subscriber_table:
            for act in Framework._subscriber_table[event.signal]:
                act.postFIFO(event)
        # Run to completion
        Framework.get_event_loop().call_soon_threadsafe(Framework.run)

    @staticmethod
    def subscribe(signame, act):
        """Adds the given Ahsm to the subscriber table list
        for the given signal.  The argument, signame, is a string of the name
        of the Signal to which the Ahsm is subscribing.  Using a string allows
        the Signal to be created in the registry if it is not already.
        """
        sigid = Signal.register(signame)
        if sigid not in Framework._subscriber_table:
            Framework._subscriber_table[sigid] = []
        Framework._subscriber_table[sigid].append(act)

    @staticmethod
    def addTimeEvent(tm_event, delta):
        """Adds the TimeEvent to the collection of time events in the Framework.
        The event will fire its signal (to the TimeEvent's target Ahsm)
        after the delay, delta.
        """
        expiration = Framework.get_event_loop().time() + delta
        Framework.addTimeEventAt(tm_event, expiration)

    @staticmethod
    def addTimeEventAt(tm_event, abs_time):
        """Adds the TimeEvent to the collection of time events in the Framework.
        The event will fire its signal (to the TimeEvent's target Ahsm)
        at the given absolute time (Framework.get_event_loop().time()).
        """
        assert tm_event not in Framework._time_event_handles
        Framework._scheduleTimeEvent(tm_event, abs_time)

    @staticmethod
    def _scheduleTimeEvent(tm_event, expiration):
        """Schedule the TimeEvent using call_at
        """
        Framework._time_event_handles[tm_event] = Framework.get_event_loop().call_at(expiration, Framework.timeEventCallback,
                                                                                     tm_event, expiration)

    @staticmethod
    def removeTimeEvent(tm_event):
        """Removes the TimeEvent from the dictionary of active time events, cancelling
            it if it is pending
        """
        if tm_event in Framework._time_event_handles:
            Framework._time_event_handles[tm_event].cancel()
            del Framework._time_event_handles[tm_event]

    @staticmethod
    def timeEventCallback(tm_event, expiration):
        """The callback function for all TimeEvents.
        Posts the event to the event's target Ahsm.
        If the TimeEvent is periodic, reschedule its next occurrence.
        """
        assert tm_event in Framework._time_event_handles, ("Exp:%f _time_event_handles.keys():%s" %
                                                           (expiration, Framework._time_event_handles.keys()))

        # Remove this expired TimeEvent from the dictionary
        del Framework._time_event_handles[tm_event]

        # Post the event to the target Ahsm
        tm_event.act.postFIFO(tm_event)

        # If this is a periodic time event, schedule its next expiration
        if tm_event.interval > 0:
            Framework._scheduleTimeEvent(tm_event, expiration + tm_event.interval)

        # Run to completion
        Framework.get_event_loop().call_soon_threadsafe(Framework.run)

    @staticmethod
    def add(act):
        """Makes the framework aware of the given Ahsm.
        """
        Framework._ahsm_registry.append(act)
        assert act.priority not in Framework._priority_dict, ("Priority MUST be unique")
        Framework._priority_dict[act.priority] = act
        Spy.on_framework_add(act)

    @staticmethod
    def run():
        """Dispatches an event to the highest priority Ahsm
        until all event queues are empty (i.e. Run To Completion).
        If any exception occurs in the state handler functions called
        while performing ``dispatch``, post the ERROR event on the FIFO
        of the state machine, with information about the exception, a traceback
        and the class name in which the exception occured, so that it can be
        dealt with appropriately.
        """
        def getPriority(x):
            return x.priority

        while True:
            allQueuesEmpty = True
            sorted_acts = sorted(Framework._ahsm_registry, key=getPriority)
            terminate = True
            for act in sorted_acts:
                if act.terminated:
                    continue
                terminate = False
                if act.has_msgs():
                    event_next = act.pop_msg()
                    act.dispatch(event_next)
                    allQueuesEmpty = False
                    break
            if terminate:
                Framework.get_terminate_event().set()
            if allQueuesEmpty:
                return

    @staticmethod
    def stop():
        """EXITs all Ahsms and sets the _terminate_event flag.
        """
        # Disable the timer callback
        for tm_event in Framework._time_event_handles:
            Framework._time_event_handles[tm_event].cancel()

        # Post TERMINATE to all Ahsms so they execute their EXIT handler
        for act in Framework._ahsm_registry:
            Framework.post(Event.TERMINATE, act)

        # Run to completion so each Ahsm will process SIGTERM
        Framework.run()
        Framework.get_terminate_event().set()
        # Framework.get_event_loop().stop()
        # Spy.on_framework_stop()

    @staticmethod
    def get_info():
        """Gets the name and current state
        of each actor in the framework.
        """
        result = {}
        for act in Framework._ahsm_registry:
            if act.state_receiving_dispatch is not None:
                result[act.__class__.__name__] = {
                    "state_handling_event": act.state.__name__,
                    "state_receiving_dispatch": act.state_receiving_dispatch.__name__
                }
            else:
                result[act.__class__.__name__] = {"state": act.state.__name__}
        return result

    @staticmethod
    def print_info():
        """Prints the name and current state
        of each actor in the framework.
        Meant to be called when ctrl+T (SIGINFO/29) is issued.
        """
        info_dict = Framework.get_info()
        for actor in info_dict:
            print(actor, info_dict[actor])

    signal.signal(signal.SIGINT, lambda *args: Framework.stop())
    signal.signal(signal.SIGTERM, lambda *args: Framework.stop())

    @staticmethod
    async def done():
        """Await this coroutine to wait for all state machines to terminate. This is written
        as a loop so that CTRL-C in Windows will be acted upon"""
        while True:
            if Framework.get_terminate_event().is_set():
                break
            await asyncio.sleep(0.5)


class Ahsm(Hsm):
    """An Augmented Hierarchical State Machine (AHSM); a.k.a. ActiveObject/AO.
    Adds a priority, message queue and methods to work with the queue.
    """
    def start(self, priority):
        # must set the priority before Framework.add() which uses the priority
        self.priority = priority
        Framework.add(self)
        self.mq = collections.deque()
        try:
            self.init()
        except Exception as e:
            event = Event(Signal.ERROR, {"exc": e, "traceback": traceback.format_exc(), "location": self.__class__.__name__})
            if self.publish_errors:
                Framework.publish(event)
            else:
                self.postFIFO(event)
        # Run to completion
        Framework.get_event_loop().call_soon_threadsafe(Framework.run)

    def postLIFO(self, evt):
        self.mq.append(evt)

    def postFIFO(self, evt):
        self.mq.appendleft(evt)

    def pop_msg(self, ):
        return self.mq.pop()

    def has_msgs(self, ):
        return len(self.mq) > 0


class Factory(Ahsm):
    _handled_signals = {}
    _parents = {}

    def __init__(self):
        super().__init__()

    @classmethod
    def _add_catch(cls, state_name, signal_name, handler_name):
        cls._handled_signals[state_name][signal_name] = handler_name

    @classmethod
    def _build_initial(cls, initial_state, setup, signal_list):
        def _initial(self, event):
            if setup:
                getattr(self, setup)()
            for sig in signal_list:
                Framework.subscribe(sig, self)
            return self.tran(initial_state)

        handler = state(copy(_initial))
        handler.__name__ = "_initial"
        handler.__qualname__ = handler.__name__
        handler.__module__ = cls.__module__
        setattr(cls, "_initial", handler)

    @classmethod
    def _build_state(cls, name, parent):
        def state_handler(self, event):
            sig_name = Signal._lookup[event.signal]
            if sig_name in cls._handled_signals[name]:
                event_handler = getattr(self, cls._handled_signals[name][sig_name])
                ret_val = event_handler(event)
                if ret_val is not None:
                    return ret_val
            return self.super(parent)

        handler = state(copy(state_handler))
        handler.__name__ = name
        handler.__qualname__ = handler.__name__
        handler.__module__ = cls.__module__
        setattr(cls, name, handler)
        cls._handled_signals[name] = {}
        cls._parents[name] = parent

    @classmethod
    def build_hsm(cls, descr):
        cls._handled_signals = {}
        cls._parents = {}
        # Build the _initial method
        cls._build_initial(descr.initial, descr.setup, descr.signals)
        for state in descr.states:
            cls._build_state(state.name, state.parent)
            for catch in state.catches:
                cls._add_catch(state.name, catch.signal, catch.handler)


class TimeEvent(object):
    """TimeEvent is a composite class that contains an Event.
    A TimeEvent is created by the application and added to the Framework.
    The Framework then emits the event after the given delay.
    A one-shot TimeEvent is created by calling either postAt() or postIn().
    A periodic TimeEvent is created by calling the postEvery() method.
    """
    def __init__(self, signame):
        assert type(signame) == str
        self.signal = Signal.register(signame)
        self.value = None

    def postAt(self, act, abs_time):
        """Posts this TimeEvent to the given Ahsm at a specified time.
        """
        assert issubclass(type(act), Ahsm)
        self.act = act
        self.interval = 0
        Framework.addTimeEventAt(self, abs_time)

    def postIn(self, act, delta):
        """Posts this TimeEvent to the given Ahsm after the time delta.
        """
        assert issubclass(type(act), Ahsm)
        self.act = act
        self.interval = 0
        Framework.addTimeEvent(self, delta)

    def postEvery(self, act, delta):
        """Posts this TimeEvent to the given Ahsm after the time delta
        and every time delta thereafter until disarmed.
        """
        assert issubclass(type(act), Ahsm)
        self.act = act
        self.interval = delta
        Framework.addTimeEvent(self, delta)

    def disarm(self):
        """Removes this TimeEvent from the Framework's active time events.
        """
        self.act = None
        Framework.removeTimeEvent(self)
