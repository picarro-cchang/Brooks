"""
Copyright 2012 Picarro Inc.

A server to emulate a variety of REST API calls that are made by DatEchoP3.
"""

from __future__ import with_statement

import time
import pprint

import simplejson as json
import flask


APP = flask.Flask(__name__)
STATS = {
    'ticketReqs' : 0,
    'localIpReqs' : 0,
    'pushDataReqs' : 0
}


@APP.route('/test/rest/sec/dummy/1.0/Admin/', methods=['GET', 'POST'])
def ticket():
    STATS['ticketReqs'] += 1
    return json.dumps({ 'ticket' : '123456789' })

@APP.route('/test/rest/gdu/<ticket>/1.0/AnzMeta/', methods=['GET', 'POST'])
def localIp(ticket):
    STATS['localIpReqs'] += 1

    if ticket == 'None':
        return 'invalid ticket', 403

    print 'As POST:'
    pprint.pprint(flask.request.form)
    return ''

@APP.route('/test/rest/gdu/<ticket>/1.0/AnzLog/', methods=['GET', 'POST'])
def pushData(ticket):
    data = flask.request.form
    STATS['pushDataReqs'] += 1
    return 'OK'

@APP.route('/stats')
def stats():
    with open('stats.json', 'wb') as f:
        json.dump(STATS, f)
    return ''

if __name__ == '__main__':
    APP.run()
