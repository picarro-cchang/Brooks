#!/usr/bin/python3
#
# FILE:
#   iwriter.py
#
# DESCRIPTION:
#   Interface class for synchronous access to a time series database
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#               chetan  Original code
#   3-Oct-2019  sze     Initial check-in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
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
