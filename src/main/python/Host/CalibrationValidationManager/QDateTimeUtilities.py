# Functions to handle typical data/time management tasks
#
from PyQt4 import QtCore

def get_nseconds_of_latest_data(timestamps = [],
                                data = [],
                                nseconds = 1):
    """
    Given a list of unix timestamps, and an associated list of data,
    return the most recent times and data spanning at least n seconds.
    :param timestamps: timestamp[0] = oldest time
    :param data:
    :param nseconds:
    :return:
    """

    # time_span_in_data is False if nseconds exceeds the available data.  If this is
    # the case the entire set of input data is returned.
    #
    time_span_in_data = False

    i = 0
    newest_timestamp = QtCore.QDateTime.fromTime_t(int(timestamps[-1]))
    for i in xrange(1, len(timestamps)-1):
        past = QtCore.QDateTime.fromTime_t(int(timestamps[-i]))
        if past.secsTo(newest_timestamp) >= nseconds:
            time_span_in_data = True
            break
    return (timestamps[-i:], data[-i:], time_span_in_data)