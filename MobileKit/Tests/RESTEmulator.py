"""
Copyright 2012 Picarro Inc.

A server to emulate a variety of REST API calls that are made by DatEchoP3.
"""

from __future__ import with_statement

import time
import datetime
import pprint
import optparse
import random

import simplejson as json
import flask

from Host.Common import ordereddict


APP = flask.Flask(__name__)
STATS = {
    'ticketReqs' : 0,
    'localIpReqs' : 0,
    'pushDataReqs' : 0,
    # The last date range request for AnzLogMeta
    'lastRangeReq' : None,
    'lastNLines' : 0
}

# We care the order in which files are sent up
FILES_ROWS = ordereddict.OrderedDict()
# For verification tests
FILES_DATA = {}

# Can be set by a test for use in subsequent calls
LAST_TIMESTAMP = None

# For unreliable mode.
MEAN_LATENCY_SEC = 1.0
SERVER_ERROR_PROB = 0.1
RTN_LAST_ROW_MISS_PROB = 0.1

ANALYZER_IDS = []

BASE_ROW = {
    'durr' : 0,
    'durrstr' : '(0h:0m)',
    'etmname' : 1343148169,
    'FILENAME_nint' : 1,
    'LOGTYPE' : 'dat',
    'maxetm' : 0,
    'minetm' : 0
}


@APP.route('/test/rest/sec/dummy/<testId>/Admin/', methods=['GET', 'POST'])
def ticket(testId):
    if (APP.config['isUnreliable']):
            time.sleep(random.expovariate(1.0 / MEAN_LATENCY_SEC))

    STATS['ticketReqs'] += 1

    if (APP.config['isUnreliable']) and random.random() <= SERVER_ERROR_PROB:
        return '', 500
    else:
        return json.dumps({ 'ticket' : '123456789' })

@APP.route('/test/rest/gdu/<ticket>/<testId>/AnzMeta/', methods=['GET', 'POST'])
def localIp(ticket, testId):
    if (APP.config['isUnreliable']):
            time.sleep(random.expovariate(1.0 / MEAN_LATENCY_SEC))

    STATS['localIpReqs'] += 1

    data = json.loads(flask.request.form['data'])
    ANALYZER_IDS.append(data[0]['ANALYZER'])

    if ticket in ['None', 'Invalid']:
        return 'invalid ticket', 403

    APP.logger.debug("FILES_ROWS = %s" % pprint.pformat(FILES_ROWS))

    if (APP.config['isUnreliable']) and random.random() <= SERVER_ERROR_PROB:
        return '', 500
    else:
        return ''

@APP.route('/test/rest/gdu/<ticket>/<testId>/AnzLog/', methods=['GET', 'POST'])
def pushData(ticket, testId):
    if (APP.config['isUnreliable']):
            time.sleep(random.expovariate(1.0 / MEAN_LATENCY_SEC))

    data = json.loads(flask.request.form['data'])

    k = data[0]['logname']
    FILES_ROWS[k] = int(data[0]['logdata'][-1]['row'])
    STATS['pushDataReqs'] += 1
    STATS['lastNLines'] = len(data[0]['logdata'])

    if k not in FILES_DATA:
        FILES_DATA[k] = []

    FILES_DATA[k].extend(data[0]['logdata'])

    if (APP.config['isUnreliable']) and random.random() <= SERVER_ERROR_PROB:
        return '', 500
    else:
        return '"OK"'

@APP.route('/test/rest/gdu/<ticket>/<float:testId>/AnzLogMeta/', methods=['GET'])
def getMetadata(ticket, testId):
    if (APP.config['isUnreliable']):
            time.sleep(random.expovariate(1.0 / MEAN_LATENCY_SEC))

    start = float(flask.request.args.get('startEtm'))
    stop = float(flask.request.args.get('endEtm'))

    STATS['lastRangeReq'] = (start, stop)

    if testId == 3.0 or testId == 14.0:
        assert LAST_TIMESTAMP is not None
        assert len(ANALYZER_IDS) > 0

        # Return 1 file that is fully complete.
        row = BASE_ROW.copy()
        row.update({ 'LOGNAME' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'name' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'ANALYZER' : ANALYZER_IDS[0],
                     'lastRow' : '16207' })

        ret = json.dumps([row])

    elif testId == 4.0:
        assert LAST_TIMESTAMP is not None
        assert len(ANALYZER_IDS) > 0

        row = BASE_ROW.copy()
        row.update({ 'LOGNAME' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'name' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'ANALYZER' : ANALYZER_IDS[0],
                     'lastRow' : '16000' })

        ret = json.dumps([row])

    elif testId == 8.0:
        return '', 404

    elif testId == 10.0:
        assert LAST_TIMESTAMP is not None
        assert len(ANALYZER_IDS) > 0

        # Return 1 file that is fully complete.
        row = BASE_ROW.copy()
        row.update({ 'LOGNAME' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'name' :
                        "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
                     'ANALYZER' : ANALYZER_IDS[0] })

        ret = json.dumps([row])

    elif testId == 15.0:
        # assert LAST_TIMESTAMP is not None
        # assert len(ANALYZER_IDS) > 0

        # row = BASE_ROW.copy()
        # row.update({ 'LOGNAME' :
        #              "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMETAMP,
        #              'name' :
        #              "TEST23-%s-DataLog_User_Minimal.dat" % LAST_TIMESTAMP,
        #              'ANALYZER' : ANALYZER_IDS[0] })
        ret = json.dumps([])

    else:
        assert len(ANALYZER_IDS) > 0

        rows = []
        for f in FILES_ROWS:
            row = BASE_ROW.copy()
            row.update({'LOGNAME': f,
                        'name': f,
                        'ANALYZER': ANALYZER_IDS[0]})

            if not (APP.config['isUnreliable'] and
                    random.random < RTN_LAST_ROW_MISS_PROB):
                row.update({'lastRow': FILES_ROWS[f]})

            rows.append(row)

        ret = json.dumps(rows)

    if (APP.config['isUnreliable']) and random.random() <= SERVER_ERROR_PROB:
        return '', 500
    else:
        return ret

@APP.route('/stats')
def stats():
    with open('stats.json', 'wb') as fp:
        STATS['pushedFiles'] = len(FILES_ROWS)
        json.dump(STATS, fp)
        for s in STATS:
            STATS[s] = 0

    return ''

@APP.route('/filesRowsStats')
def filesRowsStats():
    filesRows = []
    for k in FILES_ROWS:
        filesRows.append([k, FILES_ROWS[k]])

    with open('filesRowsStats.json', 'wb') as fp:
        json.dump(filesRows, fp)

    return json.dumps(filesRows)

@APP.route('/analyzerIds')
def analyzerIds():
    with open('analyzerIds.json', 'wb') as fp:
        json.dump(ANALYZER_IDS, fp)

    return json.dumps(ANALYZER_IDS)

# Used to set the timestamp of the next returned AnzLogMeta query.
@APP.route('/setLogDate/<int:year>/<int:month>/<int:day>'
           '/<int:hour>/<int:minute>/<int:second>')
def setLogDate(year, month, day, hour, minute, second):
    global LAST_TIMESTAMP
    LAST_TIMESTAMP = datetime.datetime(year, month, day, hour, minute,
                                       second).strftime("%Y%m%d-%H%M%SZ")
    return ''

@APP.route('/getLines/<logName>')
def getLines(logName):
    return json.dumps(FILES_DATA[logName])

@APP.route('/resetStats')
def resetStats():
    for s in STATS:
        STATS[s] = 0

    return ''

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--unreliable', action='store_true', dest='isUnreliable',
                      help='Cause the server responses to be laggy, error-prone '
                      'and generally unreliable.')

    options, _ = parser.parse_args()
    APP.config['isUnreliable'] = options.isUnreliable

    random.seed(None)

    APP.run()
