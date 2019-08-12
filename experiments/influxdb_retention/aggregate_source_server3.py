#! /usr/local/bin/python
# -*- coding: utf-8 -*-
from calendar import timegm
from collections import namedtuple
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
dbase_name = 'pigss_sim_data'
if dbase_name not in [result["name"] for result in client.get_list_database()]:
    print("Database %s not found" % dbase_name)
client.switch_database(dbase_name)
durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"]
durations_ms = [15000, 1 * 60000, 5 * 60000, 15 * 60000, 1 * 3600000, 4 * 3600000, 12 * 3600000, 24 * 3600000]


def convert_to_time_ms(timestamp):
    return 1000 * timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').timetuple())


def get_field_keys(client, measurement):
    rs = client.query("SHOW FIELD KEYS FROM %s" % measurement)
    return [(row["fieldKey"], row["fieldType"]) for key, row_gen in rs.items() for row in row_gen]


def get_tag_keys():
    rs = client.query('SHOW TAG KEYS FROM crds')
    return [row["tagKey"] for key, row_gen in rs.items() for row in row_gen]


@app.route('/')
def health_check():
    return 'This datasource is healthy.'


@app.route('/search', methods=['GET', 'POST'])
def search():
    items = get_field_keys(client, "crds")
    return jsonify([key for key, ftype in items if ftype in ['float', 'integer']])


def make_adhoc_filter(filters):
    result = []
    tag_keys = get_tag_keys()
    for filt in filters:
        # Strings for tags which are not regexs must be in single quotes
        if filt['key'] in tag_keys:
            value = filt['value']
            if isinstance(value, str) and value and value[0] != '/' and value[-1] != '/':
                value = "'" + value + "'"
            filt['value'] = value
        result.append('"{key}"{operator}{value}'.format(**filt))
    return ' AND '.join(result).strip()


@app.route('/query', methods=['GET', 'POST'])
def query():
    req = request.get_json()
    # print('Request: {}'.format(req))
    data = []
    if 'target' in req['targets'][0]:
        target = req['targets'][0]['target']
        adhoc_filter = req['adhocFilters']
        where_clauses = []
        clause = make_adhoc_filter(adhoc_filter)
        if clause:
            where_clauses.append(clause)
        aux_data = req['targets'][0].get('data')
        if aux_data and 'where' in aux_data:
            where_clauses.append(aux_data['where'])
        where_clause = " AND ".join(where_clauses)
        if where_clause:
            where_clause += ' AND '
        max_data_points = req['maxDataPoints']
        start_time_ms = int(req['scopedVars']['__from']['value'])
        stop_time_ms = int(req['scopedVars']['__to']['value'])
        interval = req['scopedVars']['__interval']['value']
        interval_ms = int(req['scopedVars']['__interval_ms']['value'])
        range_ms = stop_time_ms - start_time_ms
        # Determine which resolution to use to satisfy the request
        for which, duration_ms in enumerate(durations_ms):
            if range_ms < max_data_points * duration_ms:
                break
        print(f"which {which}, duration_ms {duration_ms}")
        # which is probably best, but check all coarser resolutions in case one
        #  has data closer to the starting time

        # Candidates contains tuples with (|start_time_ofset|, duration_ms, duration, data_points)
        #  when these are sorted into ascending order, the first entry with data_points < max_data_points
        #  is the one we use

        Candidate = namedtuple("Candidate", ['start_time_offset', 'duration_ms', 'duration', 'data_points'])
        candidates = []
        for duration, duration_ms in zip(durations[which:], durations_ms[which:]):
            rs = client.query(
                'SELECT "mean_{target}" FROM crds1_{interval} '
                'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms ORDER BY time ASC LIMIT 1'.format(
                    target=target,
                    where_clause=where_clause,
                    start_time_ms=start_time_ms,
                    stop_time_ms=stop_time_ms,
                    interval=duration),
                epoch='ms')
            times = [row['time'] for key, row_gen in rs.items() for row in row_gen]
            if times:
                candidates.append(Candidate(abs(times[0] - start_time_ms), duration_ms, duration, range_ms // duration_ms))

        if which == 0:
            # Also need to consider the undecimated data
            rs = client.query(
                'SELECT "{target}" FROM crds '
                'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms AND valve_stable_time>30 ORDER BY time ASC LIMIT 1'
                .format(target=target, where_clause=where_clause, start_time_ms=start_time_ms, stop_time_ms=stop_time_ms),
                epoch='ms')
            times = [row['time'] for key, row_gen in rs.items() for row in row_gen]
            rs = client.query(
                'SELECT COUNT("{target}") as count FROM crds '
                'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms AND valve_stable_time>30'.format(
                    target=target, where_clause=where_clause, start_time_ms=start_time_ms, stop_time_ms=stop_time_ms),
                epoch='ms')
            counts = [row['count'] for key, row_gen in rs.items() for row in row_gen]
            if times:
                candidates.append(Candidate(abs(times[0] - start_time_ms), 0, '0', counts[0] // 2))
        good_candidates = [candidate for candidate in candidates if candidate.data_points <= max_data_points]
        good_candidates.sort()
        best_duration = good_candidates[0].duration

        print(f"Good candidates are {good_candidates}. Best duration is {best_duration}")
        if best_duration == '0':
            rs = client.query(
                'SELECT mean("{target}") as mean, max("{target}") AS max, min("{target}") AS min FROM "crds" '
                'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms AND valve_stable_time>30 GROUP BY time({interval}) fill(none)'
                .format(
                    target=target,
                    where_clause=where_clause,
                    start_time_ms=start_time_ms,
                    stop_time_ms=stop_time_ms,
                    interval=interval),
                epoch='ms')
        else:
            rs = client.query(
                'SELECT sum_tot/sum_count AS mean, min, max FROM'
                ' (SELECT sum(tot) AS sum_tot, sum(count) AS sum_count, max(max) AS max, min(min) AS min FROM'
                ' (SELECT ("mean_{target}"*"count_{target}") AS tot, "count_{target}" AS count, "max_{target}" AS max, "min_{target}" AS min'
                ' FROM crds1_{interval} WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms) GROUP BY time({interval}))'
                .format(
                    target=target,
                    where_clause=where_clause,
                    start_time_ms=start_time_ms - duration_ms,
                    stop_time_ms=stop_time_ms + duration_ms,
                    interval=best_duration),
                epoch='ms')
            # print([row for key, row_gen in rs.items() for row in row_gen])

        data = [{
            "target": "mean_" + target,
            "datapoints": [[row['mean'], row['time']] for key, row_gen in rs.items() for row in row_gen]
        }, {
            "target": "max",
            "datapoints": [[row['max'], row['time']] for key, row_gen in rs.items() for row in row_gen]
        }, {
            "target": "min",
            "datapoints": [[row['min'], row['time']] for key, row_gen in rs.items() for row in row_gen]
        }]
    return jsonify(data)


@app.route('/annotations', methods=['GET', 'POST'])
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


@app.route('/tag-keys', methods=['GET', 'POST'])
def tag_keys():
    rs = client.query('SHOW TAG KEYS FROM crds')
    data = [{"type": "string", "text": tag_key} for tag_key in get_tag_keys()]
    return jsonify(data)


@app.route('/tag-values', methods=['GET', 'POST'])
def tag_values():
    req = request.get_json()
    keyname = req['key']
    rs = client.query('SHOW TAG VALUES FROM crds WITH key={keyname}'.format(keyname=keyname))
    data = [{"text": row["value"]} for key, row_gen in rs.items() for row in row_gen]
    return jsonify(data)


if __name__ == '__main__':
    app.run()
