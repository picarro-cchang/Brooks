import math
import time
from influxdb import InfluxDBClient

# https://influxdb-python.readthedocs.io/en/latest/api-documentation.html#influxdb.InfluxDBClient.close


def get_last_time(client, measurement):
    rs = client.query('select (*) from %s order by time desc limit 1' % measurement, epoch='ms')
    for key, gen in rs.items():
        for row in gen:
            return (row["time"])


def get_field_keys(client, measurement):
    rs = client.query("show field keys from %s" % measurement)
    return [(row["fieldKey"], row["fieldType"]) for key, row_gen in rs.items() for row in row_gen]


def get_last_decim(client, measurement):
    rs = client.query(
        "SELECT last_decimation FROM crds_workspace WHERE meas_name='{measurement}' ORDER BY time DESC LIMIT 5".format(
            measurement=measurement))
    return [row["last_decimation"] for key, row_gen in rs.items() for row in row_gen]


def compress_measurement(client, src_meas, dest_meas, field_key, duration, start_time_ms, stop_time_ms):
    start = time.time()
    rs = client.query('SELECT sum_tot/sum_count AS "mean_{field_key}", sum_count AS "count_{field_key}",'
                      ' min AS "min_{field_key}", max AS "max_{field_key}" INTO {dest_meas}'
                      ' FROM (SELECT sum(tot) AS sum_tot, sum(count) AS sum_count, max(max) AS max, min(min) AS min'
                      ' FROM (SELECT ("mean_{field_key}"*"count_{field_key}")  AS tot, "count_{field_key}" AS count,'
                      ' "max_{field_key}" AS max, "min_{field_key}" AS min'
                      ' FROM {src_meas} WHERE time>={start_time_ms}ms AND time<{stop_time_ms}ms GROUP BY *)'
                      ' GROUP BY time({duration}),*) GROUP BY *'.format(
                          field_key=field_key,
                          src_meas=src_meas,
                          dest_meas=dest_meas,
                          duration=duration,
                          start_time_ms=start_time_ms,
                          stop_time_ms=stop_time_ms))
    return rs.error, time.time() - start


address = "localhost"
port = 8086
client = InfluxDBClient(host=address, port=port)
dbase_name = 'pigss_sim_data'
print("get_list_database() returns %s" % client.get_list_database())
if dbase_name not in [result["name"] for result in client.get_list_database()]:
    print("Database %s not found" % dbase_name)
client.switch_database(dbase_name)
print("get_list_measurements() returns %s" % client.get_list_measurements())
measurements = client.get_list_measurements()
# rs = client.query('select (*) from crds where time>=%dms-10m and time<=%dms limit 5 offset 10' % (tlast, tlast), epoch='ms')
# rs = client.query('select (*) from crds limit 10', epoch='ms')
# rs = client.query("show field keys from crds")
#
# Start the first level of decimation
#
tlast = get_last_time(client, "crds")
measurement = "crds"
last_decim = get_last_decim(client, measurement)

start_time_ms = last_decim[0] if last_decim else 0
stop_time_ms = int(15000 * math.floor(tlast / 15000))
print('Stop timestamp: %d' % stop_time_ms)
start = time.time()
rs = client.query("SELECT min(*),max(*),mean(*),count(*) INTO crds_15s FROM crds " +
                  "WHERE time>=%dms AND time<%dms GROUP BY time(15s),*" % (start_time_ms, stop_time_ms))
print("Done compression in %.3f s, error code %s" % (time.time() - start, rs.error))
client.write_points([{
    "measurement": "crds_workspace",
    "fields": {
        "last_decimation": int(stop_time_ms)
    },
    "tags": {
        "meas_name": "crds"
    }
}])

durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"]
durations_ms = [15000, 1 * 60000, 5 * 60000, 15 * 60000, 1 * 3600000, 4 * 3600000, 12 * 3600000, 24 * 3600000]

for src_duration, dest_duration, dest_duration_ms in zip(durations[:-1], durations[1:], durations_ms[1:]):
    src_meas = measurement + "_" + src_duration
    dest_meas = measurement + "_" + dest_duration
    tlast = get_last_time(client, src_meas)
    if tlast is None:
        continue
    last_decim = get_last_decim(client, src_meas)
    start_time_ms = last_decim[0] if last_decim else 0
    stop_time_ms = int(dest_duration_ms * math.floor(tlast / dest_duration_ms))
    print(dest_duration, start_time_ms)
    if stop_time_ms > start_time_ms:
        for field_key, field_type in get_field_keys(client, "crds"):
            if field_type in ['float', 'integer']:
                err, comp_time = compress_measurement(client, src_meas, dest_meas, field_key, dest_duration, start_time_ms,
                                                      stop_time_ms)
                #print(err, comp_time)
                #print("Compression time: {:.3f}, Error: {}".format(comp_time, err))

    client.write_points([{
        "measurement": "crds_workspace",
        "fields": {
            "last_decimation": int(stop_time_ms)
        },
        "tags": {
            "meas_name": src_meas
        }
    }])
