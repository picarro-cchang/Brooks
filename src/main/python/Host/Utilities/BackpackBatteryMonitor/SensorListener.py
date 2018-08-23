import math
import Queue
import time
import types
from Host.autogen import interface
from Host.Common import CmdFIFO, SharedTypes, timestamp
from Host.Common.Listener import Listener

Driver = CmdFIFO.CmdFIFOServerProxy("http://localhost:%d" % SharedTypes.RPC_PORT_DRIVER,
                                    'SensorListener', IsDontCareConnection = False)

def lookup(value_or_name):
    """Convert value_or_name into an value, raising an exception if the name is not found"""
    if isinstance(value_or_name,types.StringType):
        try:
            value_or_name = getattr(interface,value_or_name)
        except AttributeError:
            raise AttributeError("Value identifier not recognized %r" % value_or_name)
    return value_or_name

queue = Queue.Queue(100)
listener = Listener(queue=queue,
                    port = SharedTypes.BROADCAST_PORT_SENSORSTREAM,
                    elementType = interface.SensorEntryType,
                    retry = True,
                    name = "Sensor stream listener")

reg_list = ["BATTERY_MONITOR_STATUS_REGISTER",
            "BATTERY_MONITOR_CHARGE_REGISTER",
            "BATTERY_MONITOR_VOLTAGE_REGISTER",
            "BATTERY_MONITOR_CURRENT_REGISTER",
            "BATTERY_MONITOR_TEMPERATURE_REGISTER"]

#stream_list = [lookup(name) for name in ["STREAM_DasTemp"]]
stream_list = []
now = time.time()
when = math.floor(now + 1.0)
while True:
    try:
        wait = when - now
        if wait <= 0:
            raise Queue.Empty
        data = queue.get(timeout = min(when-now, 1.0))
        utime = timestamp.unixTime(data.timestamp)
        stream_num = data.streamNum
        value = data.value
        if stream_num in stream_list:
            print utime, stream_num, value
        now = time.time()
    except Queue.Empty:
        now = time.time()
        if now > when:
            for reg in reg_list:
                print "%s: %s" % (reg, Driver.rdDasReg(reg))
            when = math.floor(now + 1.0)