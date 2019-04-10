#! /usr/local/bin/python
# -*- coding: utf-8 -*-
from calendar import timegm
from datetime import datetime
import _strptime  # https://bugs.python.org/issue7980
from flask import Flask, request, jsonify
import time
from influxdb import InfluxDBClient

# Communication with the influx database
app = Flask(__name__)
app.debug = True
address = "localhost"
port = 8086
client = InfluxDBClient(host=address, port=port)
dbase_name = 'pigss_data'
if dbase_name not in [result["name"] for result in client.get_list_database()]:
    print("Database %s not found" % dbase_name)
client.switch_database(dbase_name)
durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"]
durations_ms = [
    15000, 1 * 60000, 5 * 60000, 15 * 60000, 1 * 3600000, 4 * 3600000,
    12 * 3600000, 24 * 3600000
]


def convert_to_time_ms(timestamp):
    return 1000 * timegm(
        datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').timetuple())


def get_field_keys(client, measurement):
    rs = client.query("show field keys from %s" % measurement)
    return [(row["fieldKey"], row["fieldType"]) for key, row_gen in rs.items()
            for row in row_gen]


def get_tag_keys():
    rs = client.query('SHOW TAG KEYS FROM crds')
    return [row["tagKey"] for key, row_gen in rs.items() for row in row_gen]


@app.route('/')
def health_check():
    return 'This datasource is healthy.'


@app.route('/search', methods=['POST'])
def search():
    items = get_field_keys(client, "crds")
    return jsonify(
        [key for key, ftype in items if ftype in ['float', 'integer']])


def make_adhoc_filter(filters):
    result = []
    tag_keys = get_tag_keys()
    for filt in filters:
        # Strings for tags which are not regexs must be in single quotes
        if filt['key'] in tag_keys:
            value = filt['value']
            if isinstance(
                    value,
                    str) and value and value[0] != '/' and value[-1] != '/':
                value = "'" + value + "'"
            filt['value'] = value
        result.append('"{key}"{operator}{value}'.format(**filt))
    return ' AND '.join(result).strip()


@app.route('/query', methods=['POST'])
def query():
    req = request.get_json()
    print('Request: {}'.format(req))
    data = []
    if 'target' in req['targets'][0]:
        target = req['targets'][0]['target']
        adhoc_filter = req['adhocFilters']
        where_clause = make_adhoc_filter(adhoc_filter)
        aux_data = req['targets'][0].get('data')
        if aux_data and 'where' in aux_data:
            where_clause += ' AND ' + aux_data['where']
        if where_clause:
            where_clause += ' AND '
        max_data_points = req['maxDataPoints']
        start_time_ms = int(req['scopedVars']['__from']['value'])
        stop_time_ms = int(req['scopedVars']['__to']['value'])
        interval = req['scopedVars']['__interval']['value']
        range_ms = stop_time_ms - start_time_ms
        if range_ms / 1000 < max_data_points:
            rs = client.query(
                'SELECT mean("{target}") as mean, max("{target}") AS max, min("{target}") AS min FROM "crds" '
                'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms GROUP BY time({interval}) fill(none)'
                .format(
                    target=target,
                    where_clause=where_clause,
                    start_time_ms=start_time_ms,
                    stop_time_ms=stop_time_ms,
                    interval=interval),
                epoch='ms')
        else:
            for duration, duration_ms in zip(durations, durations_ms):
                if range_ms / duration_ms < max_data_points:
                    break
            # print(duration)
            rs = client.query(
                'SELECT sum_tot/sum_count AS mean, min, max FROM'
                ' (SELECT sum(tot) AS sum_tot, sum(count) AS sum_count, max(max) AS max, min(min) AS min FROM'
                ' (SELECT ("mean_{target}"*"count_{target}") AS tot, "count_{target}" AS count, "max_{target}" AS max, "min_{target}" AS min'
                ' FROM crds_{interval} WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms) GROUP BY time({interval}))'
                .format(
                    target=target,
                    meas='crds_1m',
                    where_clause=where_clause,
                    start_time_ms=start_time_ms,
                    stop_time_ms=stop_time_ms,
                    interval=duration),
                epoch='ms')
            # print([row for key, row_gen in rs.items() for row in row_gen])

        data = [{
            "target":
            "mean_" + target,
            "datapoints": [[row['mean'], row['time']] for key, row_gen in rs.items() for row in row_gen]},
                {
                    "target":
                    "max",
                    "datapoints": [[row['max'], row['time']]
                                   for key, row_gen in rs.items()
                                   for row in row_gen]
                },
                {
                    "target":
                    "min",
                    "datapoints": [[row['min'], row['time']]
                                   for key, row_gen in rs.items()
                                   for row in row_gen]
                }]
    return jsonify(data)


@app.route('/annotations', methods=['POST'])
def annotations():
    req = request.get_json()
    data = [{
        "annotation": 'This is the annotation',
        "time": (req['range' ['from']] + req['range' ['to']]) / 2,
        "title": 'Deployment notes',
        "tags": ['tag1', 'tag2'],
        "text": 'Hm, something went wrong...'
    }]
    return jsonify(data)


@app.route('/tag-keys', methods=['POST'])
def tag_keys():
    rs = client.query('SHOW TAG KEYS FROM crds')
    data = [{"type": "string", "text": tag_key} for tag_key in get_tag_keys()]
    return jsonify(data)


@app.route('/tag-values', methods=['POST'])
def tag_values():
    req = request.get_json()
    keyname = req['key']
    rs = client.query(
        'SHOW TAG VALUES FROM crds WITH key={keyname}'.format(keyname=keyname))
    data = [{
        "text": row["value"]
    } for key, row_gen in rs.items() for row in row_gen]
    return jsonify(data)


if __name__ == '__main__':
    app.run()