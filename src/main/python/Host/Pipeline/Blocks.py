from collections import deque
import inspect
import Queue
import sys
import threading
import time
from traitlets import (Any, Bool, Dict, Float, ForwardDeclaredInstance,
                       Instance, Integer, List, Tuple, Unicode, Union)
from traitlets.config.configurable import Configurable
from types import FunctionType, MethodType

START_TIME = time.time()


class Pipeline(Configurable):
    """Base class for constructing pipelines consisting of interconnected Blocks. The methods
       ``makeBlocks`` and ``linkBlocks`` should be defined in the subclass.
    """
    blocks = List(trait=ForwardDeclaredInstance('Block'), default_value=[])
    lock = Any()
    exc_info = Tuple()

    def __init__(self, **kwargs):
        super(Pipeline, self).__init__(**kwargs)
        self.lock = threading.Lock()

    def registerBlock(self, block):
        """Registers a block as being a member of the pipeline. This is automatically called by the
        constructor of the :py:class:`.Block`

        The list of blocks in the pipeline is used to check for completion of tasks, and to
        inform the blocks of an exception.

        :param Block block: Block to register
        """
        self.lock.acquire()
        self.blocks.append(block)
        self.lock.release()

    def signalException(self, exc_info):
        """Called by block task function to indicate that an exception has occured.

        The exception tuple is saved and sent to all blocks in the pipeline to place them in the
        faulted state.

        :param exc_info: Exception tuple from sys.exc_info()
        """
        if not self.exc_info:
            self.exc_info = exc_info
            for block in self.blocks:
                block.fault(exc_info)   # Tell all blocks about error

    def isComplete(self):
        """
        :returns: True if all block tasks are no longer running
        """
        for block in self.blocks:
            if block.thread.isAlive():
                return False
        return True

    def makeBlocks(self):
        """This method must be defined in a subclass to instantiate all the blocks for the pipeline
        and assign them to attributes of the class.
        """
        raise NotImplementedError("This must be defined in a subclass")

    def linkBlocks(self):
        """This method must be defined in a subclass to join the blocks and define the topology of
        the pipeline
        """
        raise NotImplementedError("This must be defined in a subclass")

    def waitCompletion(self, timeout=None):
        """Wait for the pipeline to finish processing data. Use ``isComplete()`` to check if
            this returns after completion or due to a timeout. Raises an exception (including traceback
            information) if one has been raised by any of the blocks in the pipeline.

            :param timeout: (optional) Timeout in seconds
        """
        try:
            for block in self.blocks:
                block.waitCompletion(timeout)
                if block.thread.isAlive():
                    return False
            return True
        finally:
            if self.exc_info:
                raise self.exc_info[1], None, self.exc_info[2]

class BlockInput(Configurable):
    """Class for inputs to blocks"""
    parent = ForwardDeclaredInstance("Block", allow_none=True)
    completed = Bool(False)
    index = Integer(0)

    def __init__(self, parent, index, **kwargs):
        super(BlockInput, self).__init__(**kwargs)
        self.parent = parent
        self.index = index

    def complete(self):
        """Called to indicate that no more is to be sent to this input"""
        self.completed = True

    def post(self, msg):
        """Post a message (usually a dictionary) to this block input

        :param msg: Message to post
        """
        if self.completed or self.parent.isFaulted():
            raise RuntimeError("Cannot post after calling complete or an exception has occured")
        else:
            self.parent.enqueue(msg, self.index)

class Block(Configurable):
    """Base class for blocks which can be connected into a pipeline.

    When a block is constructed within :py:meth:`.Pipeline.makeBlocks`, it
    registers itself with the pipeline object and saves it as the attribute
    :py:attr:`pipeline`.
    """
    pipeline = Instance(Pipeline, allow_none=True)
    thread = Instance(threading.Thread, allow_none=True)
    inputs = List(Instance(BlockInput), default_value=[])
    nextConsumer = Integer(0)
    consumers = Dict(Instance(BlockInput), default_value={})
    consumersLock = Any()
    continuationFunc = Union([Instance(FunctionType), Instance(MethodType)])
    stopLoop = Bool(False)
    exc_info = Tuple()

    def __init__(self, **kwargs):
        super(Block, self).__init__(**kwargs)
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.consumersLock = threading.Lock()
        self.continuationFunc = self.defaultContinuation
        stk = inspect.stack()
        try:
            for frame in stk:
                if 'self' in frame[0].f_locals:
                    obj = frame[0].f_locals['self']
                    if isinstance(obj, Pipeline):
                        obj.registerBlock(self)
                        self.pipeline = obj
        finally:
            del stk

    def start(self):
        """Start the thread which runs the main loop of the block"""
        self.thread.start()

    def run(self):
        try:
            self.mainLoop()
            if self.continuationFunc is not None:
                self.continuationFunc(self)
        except Exception:
            self.fault(sys.exc_info())
            if self.pipeline:
                self.pipeline.signalException(self.exc_info)
            else:
                raise self.exc_info[1], None, self.exc_info[2]

    def mainLoop(self):
        """Task method to run. Must be implemented in a subclass as a loop which
        performs the processing for the block. This loop should stop if the ``isFaulted()``
        method returns True.
        """
        raise NotImplementedError('mainLoop method must be defined in a subclass. ' +
                                  'Remember to check isFaulted and stop if necessary.')

    def linkTo(self, dest):
        """Link the output of this block to an input of another block

        :param dest: Block input or single-input block to link to.
        :type dest: BlockInput or SingleInputBlock
        :returns: Number of links so far made for this output
        """
        if isinstance(dest, SingleInputBlock):
            dest = dest.inputs[0]
        assert isinstance(dest, BlockInput)
        self.consumersLock.acquire()
        index = self.nextConsumer
        self.consumers[index] = dest
        self.nextConsumer += 1
        self.consumersLock.release()
        return index

    def isComplete(self):
        """
        :returns: True if block task is no longer running
        """
        return not self.thread.isAlive()

    def isFinishing(self):
        return all([inp.completed for inp in self.inputs])

    def isFaulted(self):
        """
        :returns: True if an exception has occured
        """
        return self.stopLoop or bool(self.exc_info)

    def fault(self, exc_info):
        """Place this block into an error state because an exception has occured. This should
            cause the main loop to exit.

            :param exc_info: Exception tuple (from sys.exc_info())
        """
        self.exc_info = exc_info

    def setContinuation(self, continuationFunc):
        """Specifies function to be executed when this block completes

        :param continuationFunc: Method or function to execute on completion
        """
        self.continuationFunc = continuationFunc

    def stop(self):
        """Stop the mainLoop"""
        self.stopLoop = True

    def waitCompletion(self, timeout=None):
        """Wait for block to finish processing data. Use ``isComplete()`` to check if
            this returns after completion or due to a timeout.

            :param timeout: (optional) Timeout in seconds
        """
        return self.thread.join(timeout)

    def defaultContinuation(self, _=None):
        if self.consumers:
            self.consumersLock.acquire()
            for i in self.consumers:
                c = self.consumers[i]
                c.complete()
            self.consumersLock.release()

class SourceBlock(Block):
    """Block which periodically calls a function that generates an output message

    :param float dt: Time in seconds between output messages
    :param func: Function which is called with the current time, and which should return a
                 message as a dictionary or tuple
    :type func: function or method
    """
    nstep = Integer(0)
    dt = Float(0.0)
    func = Union([Instance(FunctionType), Instance(MethodType)])

    def __init__(self, dt, func, **kwargs):
        super(SourceBlock, self).__init__(**kwargs)
        self.dt = dt
        self.func = func
        self.start()

    def mainLoop(self):
        """The main loop waits until the next multiple of ``dt`` since the start time,
        calls ``func`` and outputs the message."""
        start_time = sys.modules[__name__].START_TIME

        while not self.isFaulted():
            when = self.nstep * self.dt
            wait_time = (start_time + when) - time.time()
            if wait_time <= 0:
                result = self.func(when)
                if not isinstance(result, (dict, tuple)):
                    raise ValueError("Message type from a source block should be a dict or tuple")
                self.nstep += 1
                self.consumersLock.acquire()
                for i in self.consumers:
                    c = self.consumers[i]
                    c.post(result)
                self.consumersLock.release()
            else:
                time.sleep(wait_time)

class SingleInputBlock(Block):
    """Block which has a single input.

    A queue is used to serialize the input messages, and a processing function is used to compute
    the response to the input. This is still an abstract class and is the base class for
    :py:class:`.ActionBlock`, :py:class:`.TransformBlock` and :py:class:`.TransformManyBlock`

    :param func: Function which is called with the input message
    :type func: function or method
    :param int qLength: Length of input queue (default=10)
    """
    func = Union([Instance(FunctionType), Instance(MethodType)])
    inQueue = Instance(Queue.Queue)
    def __init__(self, func, qLength=10, **kwargs):
        super(SingleInputBlock, self).__init__(**kwargs)
        self.func = func
        self.inputs.append(BlockInput(self, index=0))
        self.inQueue = Queue.Queue(qLength)

    def complete(self):
        """Called to indicate that no further messages are to be sent to the block"""
        self.inputs[0].complete()

    def mainLoop(self):
        """Main loop function which must be defined in a subclass"""
        raise NotImplementedError("This must be defined in a subclass")

    def post(self, msg):
        """Called to post an input message to the block

        :param msg: Message to post
        """
        self.inputs[0].post(msg)

    def enqueue(self, msg, index):
        assert index == 0
        self.inQueue.put(msg)

class ActionBlock(SingleInputBlock):
    """A block with an input but no outputs"""
    def __init__(self, func, qLength=10, **kwargs):
        super(ActionBlock, self).__init__(func, qLength, **kwargs)
        self.start()

    def mainLoop(self):
        while not self.isFaulted():
            if self.isFinishing() and self.inQueue.empty():
                break
            try:
                msg = self.inQueue.get(timeout=0.5)
            except Queue.Empty:
                continue
            self.func(msg)

class _TransformBlock(SingleInputBlock):
    """Base class for a block with an input and an output."""
    def __init__(self, func, qLength=10, **kwargs):
        super(_TransformBlock, self).__init__(func, qLength, **kwargs)
    def mainLoop(self):
        raise NotImplementedError("This must be defined in a subclass")

class TransformBlock(_TransformBlock):
    """A block in which a single input message gives rise to a single output message"""
    def __init__(self, func, qLength=10, **kwargs):
        super(TransformBlock, self).__init__(func, qLength, **kwargs)
        self.start()

    def mainLoop(self):
        while not self.isFaulted():
            if self.isFinishing() and self.inQueue.empty():
                break
            try:
                msg = self.inQueue.get(timeout=0.5)
            except Queue.Empty:
                continue
            result = self.func(msg)
            self.consumersLock.acquire()
            for i in self.consumers:
                c = self.consumers[i]
                c.post(result)
            self.consumersLock.release()

class TransformManyBlock(_TransformBlock):
    """A block in which a single input message gives rise to a zero or more output messages"""
    def __init__(self, func, qLength=10, **kwargs):
        super(TransformManyBlock, self).__init__(func, qLength, **kwargs)
        self.start()

    def mainLoop(self):
        while not self.isFaulted():
            if self.isFinishing() and self.inQueue.empty():
                break
            try:
                msg = self.inQueue.get(timeout=0.5)
            except Queue.Empty:
                continue
            for result in self.func(msg):
                self.consumersLock.acquire()
                for i in self.consumers:
                    c = self.consumers[i]
                    c.post(result)
                self.consumersLock.release()

class MergeBlock(Block):
    """A block with many inputs. Results are sent to func in deques. Processing results in zero or more output messages"""
    func = Union([Instance(FunctionType), Instance(MethodType)])
    argDeques = List(Instance(deque), default_value=[])
    inQueue = Instance(Queue.Queue)

    def __init__(self, func, nInputs, qLength=10, **kwargs):
        super(MergeBlock, self).__init__(**kwargs)
        self.func = func
        self.continuationFunc = self.defaultContinuation
        # Count the number of positional arguments
        # argspec = inspect.getargspec(func)
        #for i in range(len(argspec.args)):
        for i in range(nInputs):
            self.inputs.append(BlockInput(self, index=i))
            self.argDeques.append(deque())
        # We vector all the inputs into a single queue so we can wait on it
        self.inQueue = Queue.Queue(qLength)
        self.start()

    def enqueue(self, msg, index):
        assert index < len(self.inputs)
        self.inQueue.put((index, msg))

    def callFunc(self, lastCall=False):
        result = self.func(*self.argDeques, lastCall=lastCall)
        if result is not None:
            for r in result:
                self.consumersLock.acquire()
                for i in self.consumers:
                    c = self.consumers[i]
                    c.post(r)
                self.consumersLock.release()

    def mainLoop(self):
        while not self.isFaulted():
            if self.isFinishing() and self.inQueue.empty():
                break
            nMsg = 0
            try:
                while not self.inQueue.empty():
                    index, msg = self.inQueue.get(timeout=0.5)
                    self.argDeques[index].append(msg)
                    nMsg += 1
            except Queue.Empty:
                continue
            if nMsg>0:
                self.callFunc()

    def defaultContinuation(self, srcBlock):
        """Default continuation propagates completion and exception conditions to all consumers.

        For the MergeManyBlock, we make a final call to the user-specified function with lastCall=True
        so that the fnal entries in the deques can be processed.
        """
        self.callFunc(lastCall=True)
        Block.defaultContinuation(self, srcBlock)

def MergeManyBlock(nInputs):
    return lambda func: MergeBlock(func, nInputs)
