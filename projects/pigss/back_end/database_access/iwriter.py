#!/usr/bin/python3
"""
Interface class for synchronous access to a time series database
"""
import abc


class IWriter(abc.ABC):
    """
    Interface to writer objects
    All data writer needs to implement so other module works same way even if new writer is used
    """
    @abc.abstractmethod
    def write_data(self, data_dict):
        """
        Abstract method to write data
        :param data_dict:
        :return:
        """
        pass

    @abc.abstractmethod
    def close_connection(self):
        """
        Abstract method to close connection
        :return:
        """
        pass

    @abc.abstractmethod
    def read_data(self, query=None, **args):
        pass
