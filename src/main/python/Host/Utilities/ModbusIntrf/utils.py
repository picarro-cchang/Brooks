#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Modbus TestKit: Implementation of Modbus protocol in python

 (C)2009 - Luc Jean - luc.jean@gmail.com
 (C)2009 - Apidev - http://www.apidev.fr

 This is distributed under GNU LGPL license, see license.txt
"""

import threading
import logging
import socket
import select


def threadsafe_function(fcn):
    """decorator making sure that the decorated function is thread safe"""
    lock = threading.Lock()

    def new(*args, **kwargs):
        """lock and call the decorated function"""
        lock.acquire()
        try:
            ret = fcn(*args, **kwargs)
        except Exception, excpt:
            raise excpt
        finally:
            lock.release()
        return ret

    return new


def flush_socket(socks, lim=0):
    """remove the data present on the socket"""
    input_socks = [socks]
    cnt = 0
    while 1:
        i_socks, o_socks, e_socks = select.select(input_socks, input_socks, input_socks, 0.0)
        if len(i_socks) == 0:
            break
        for sock in i_socks:
            sock.recv(1024)
        if lim > 0:
            cnt += 1
            if cnt >= lim:
                #avoid infinite loop due to loss of connection
                raise Exception("flush_socket: maximum number of iterations reached")


def get_log_buffer(prefix, buff):
    """Format binary data into a string for debug purpose"""
    log = prefix
    for i in buff:
        log += str(ord(i)) + "-"
    return log[:-1]


class ConsoleHandler(logging.Handler):
    """This class is a logger handler. It prints on the console"""
    def __init__(self):
        """Constructor"""
        logging.Handler.__init__(self)

    def emit(self, record):
        """format and print the record on the console"""
        print self.format(record)


class LogitHandler(logging.Handler):
    """This class is a logger handler. It send to a udp socket"""
    def __init__(self, dest):
        """Constructor"""
        logging.Handler.__init__(self)
        self._dest = dest
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        """format and send the record over udp"""
        self._sock.sendto(self.format(record) + "\r\n", self._dest)


class DummyHandler(logging.Handler):
    """This class is a logger handler. It doesn't do anything"""
    def __init__(self):
        """Constructor"""
        logging.Handler.__init__(self)

    def emit(self, record):
        """do nothinbg with the given record"""
        pass

def create_logger(name="dummy", level=logging.DEBUG, \
                  record_format="%(asctime)s\t%(levelname)s\t%(module)s.%(funcName)s\t%(threadName)s\t%(message)s"):
    """Create a logger according to the given settings"""
    logger = logging.getLogger("modbus_tk")
    logger.setLevel(level)
    formatter = logging.Formatter(record_format)
    if name == "udp":
        log_handler = LogitHandler(("127.0.0.1", 1975))
    elif name == "console":
        log_handler = ConsoleHandler()
    elif name == "dummy":
        log_handler = DummyHandler()
    else:
        raise Exception("Unknown handler %s" % name)
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    return logger


def swap_bytes(word_val):
    """swap lsb and msb of a word"""
    msb = word_val >> 8
    lsb = word_val % 256
    return (lsb << 8) + msb


def calculate_crc(data):
    """Calculate the CRC16 of a datagram"""
    crc = 0xFFFF
    for i in data:
        crc = crc ^ ord(i)
        for j in xrange(8):
            tmp = crc & 1
            crc = crc >> 1
            if tmp:
                crc = crc ^ 0xA001
    return swap_bytes(crc)


def calculate_rtu_inter_char(baudrate):
    """calculates the interchar delay from the baudrate"""
    if baudrate <= 19200:
        return 11.0 / baudrate
    else:
        return 0.0005


class WorkerThread:
    """
    A thread which is running an almost-ever loop
    It can be stopped by calling the stop function
    """
    def __init__(self, main_fct, args=(), init_fct=None, exit_fct=None):
        """Constructor"""
        self._fcts = [init_fct, main_fct, exit_fct]
        self._args = args
        self._thread = threading.Thread(target=WorkerThread._run, args=(self, ))
        self._go = threading.Event()

    def start(self):
        """Start the thread"""
        self._go.set()
        self._thread.start()

    def stop(self):
        """stop the thread"""
        if self._thread.isAlive():
            self._go.clear()
            self._thread.join()

    def _run(self):
        """main function of the thread execute _main_fct until stop is called"""
        try:
            if self._fcts[0]:
                self._fcts[0](*self._args)
            while self._go.isSet():
                self._fcts[1](*self._args)
        except Exception, excpt:
            #LOGGER.error("error: %s" % str(excpt))
            print "error: %s" % str(excpt)
        finally:
            if self._fcts[2]:
                self._fcts[2](*self._args)
