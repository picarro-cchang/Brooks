import asyncio
from collections import namedtuple

from aiohttp import web
from aioinflux import InfluxDBClient, iterpoints

import experiments.influxdb_retention.duration_tools as dt
from experiments.common.service_template import ServiceTemplate


class TimeAggregationService(ServiceTemplate):
    def __init__(self):
        super().__init__()

    def setup_routes(self):
        self.app.router.add_route("GET", "/", self.health_check)
        self.app.router.add_route("GET", "/search", self.search)
        self.app.router.add_route("POST", "/search", self.search)
        self.app.router.add_route("GET", "/tag-keys", self.tag_keys)
        self.app.router.add_route("POST", "/tag-keys", self.tag_keys)
        self.app.router.add_route("POST", "/tag-values", self.tag_values)
        self.app.router.add_route("POST", "/query", self.query)

    async def on_startup(self, app):
        db_config = self.app['farm'].config.get_time_series_database()
        self.client = InfluxDBClient(host=db_config["server"], port=db_config["port"], db=db_config["name"])
        self.default_durations = ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "1d"]
        self.default_durations_ms = [dt.generate_duration_in_seconds(d, ms=True) for d in self.default_durations]

    async def on_shutdown(self, app):
        print("Time Aggregation Service is shutting down")

    async def health_check(self, request):
        return web.Response(text='This datasource is healthy.')

    async def search(self, request):
        """
        ---
        description: Returns field names in the crds measurement

        tags:
            -   Time aggregated data source server
        summary: Get field names in crds measurement
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        items = await self.get_field_keys("crds")
        return web.json_response([key for key, ftype in items if ftype in ['float', 'integer']])

    async def tag_keys(self, request):
        """
        ---
        description: Returns tag names in the crds measurement

        tags:
            -   Time aggregated data source server
        summary: Get tag names in crds measurement
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        tag_keys = await self.get_tag_keys()
        return web.json_response([{"type": "string", "text": tag_key} for tag_key in tag_keys])

    async def tag_values(self, request):
        """
        ---
        description: request values associated with a given tag

        tags:
            -   Time aggregated data source server
        summary: request values for a given tag
        consumes:
            -   application/json
        produces:
            -   application/json
        parameters:
            -   in: body
                name: tag
                description: Specify tag
                required: true
                schema:
                    type: object
                    properties:
                        key:
                            type:   string
                            required:   true
        responses:
            "200":
                description: successful operation
        """
        body = await request.json()
        print(f"Body: {body}")
        tag_name = body.get("key", None)
        print(tag_name)
        rs = await self.client.query(f'SHOW TAG VALUES FROM crds WITH key={tag_name}')
        print(rs)
        data = [{'text': result[1]} for result in iterpoints(rs)]
        return web.json_response(data)

    async def query(self, request):
        """
        ---
        description: Make a query to the database

        tags:
            -   Time aggregated data source server
        summary: make a query to the database
        consumes:
            -   application/json
        produces:
            -   application/json
        parameters:
            -   in: body
                name: query
                description: Specify query
                required: true
                schema:
                    type: object
                    properties:
                        scopedVars:
                            type: object
                            properties:
                                __from:
                                    type: object
                                    properties:
                                        value:
                                            type: integer
                                __to:
                                    type: object
                                    properties:
                                        value:
                                            type: integer
                                __interval:
                                    type: object
                                    properties:
                                        value:
                                            type: integer
                        maxDataPoints:
                            type: integer
                        targets:
                            type: array
                            items:
                                type: object
                                properties:
                                    target:
                                        type: string
                        adHocFilters:
                            type: array
                            items:
                                type: object
        responses:
            "200":
                description: successful operation
        """
        req = await request.json()
        # print('Request: {}'.format(req))
        data = []
        if 'target' in req['targets'][0]:
            target = req['targets'][0]['target']
            adhoc_filter = req['adhocFilters']
            where_clauses = []
            clause = await self.make_adhoc_filter(adhoc_filter)
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
            # interval_ms = int(req['scopedVars']['__interval_ms']['value'])
            range_ms = stop_time_ms - start_time_ms
            # Determine which resolution to use to satisfy the request
            for which, duration_ms in enumerate(self.default_durations_ms):
                if range_ms < max_data_points * duration_ms:
                    break
            # which is probably best, but check all coarser resolutions in case one
            #  has data closer to the starting time

            # Candidates contains tuples with (|start_time_ofset|, duration_ms, duration, data_points)
            #  when these are sorted into ascending order, the first entry with data_points < max_data_points
            #  is the one we use

            # Candidate = namedtuple("Candidate", ['start_time_offset', 'duration_ms', 'duration', 'data_points'])
            Candidate = namedtuple("Candidate", ['duration_ms', 'duration', 'data_points'])
            candidates = []
            for duration, duration_ms in zip(self.default_durations[which:], self.default_durations_ms[which:]):
                rs = await self.client.query(
                    f'SELECT "mean_{target}" FROM crds_{duration}.crds_{duration} '
                    f'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms ORDER BY time ASC LIMIT 1',
                    epoch='ms')
                times = [result[0] for result in iterpoints(rs)]
                if times:
                    # candidates.append(Candidate(abs(times[0] - start_time_ms), duration_ms, duration, range_ms // duration_ms))
                    candidates.append(Candidate(duration_ms, duration, range_ms // duration_ms))
            if which == 0:
                # Also need to consider the undecimated data
                rs = await self.client.query(
                    f'SELECT "{target}" FROM crds '
                    f'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms ORDER BY time ASC LIMIT 1',
                    epoch='ms')
                times = [result[0] for result in iterpoints(rs)]
                rs = await self.client.query(
                    f'SELECT COUNT("{target}") as count FROM crds '
                    f'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms',
                    epoch='ms')
                counts = [result[1] for result in iterpoints(rs)]
                if times:
                    # candidates.append(Candidate(abs(times[0] - start_time_ms), 0, '0', counts[0] // 2))
                    candidates.append(Candidate(0, '0', counts[0] // 2))
            good_candidates = [candidate for candidate in candidates if candidate.data_points <= max_data_points]
            good_candidates.sort()
            best_duration = good_candidates[0].duration

            if best_duration == '0':
                rs = await self.client.query(
                    f'SELECT mean("{target}") as mean, max("{target}") AS max, min("{target}") AS min FROM "crds" '
                    f'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms GROUP BY time({interval}) fill(none)',
                    epoch='ms')
            else:
                rs = await self.client.query(
                    f'SELECT sum_tot/sum_count AS mean, min, max FROM'
                    f' (SELECT sum(tot) AS sum_tot, sum(count) AS sum_count, max(max) AS max, min(min) AS min FROM'
                    f' (SELECT ("mean_{target}"*"count_{target}") AS tot, "count_{target}" AS count, "max_{target}" AS max, "min_{target}" AS min'
                    f' FROM crds_{best_duration}.crds_{best_duration} WHERE {where_clause} time>={start_time_ms-duration_ms}ms AND time<{stop_time_ms+duration_ms}ms)'
                    f' GROUP BY time({best_duration}))',
                    epoch='ms')
                # print([row for key, row_gen in rs.items() for row in row_gen])

            data = [{
                "target": "mean_" + target,
                "datapoints": [[result[1], result[0]] for result in iterpoints(rs)]
            }, {
                "target": "max",
                "datapoints": [[result[3], result[0]] for result in iterpoints(rs)]
            }, {
                "target": "min",
                "datapoints": [[result[2], result[0]] for result in iterpoints(rs)]
            }]
        return web.json_response(data)

    async def get_field_keys(self, measurement):
        rs = await self.client.query("SHOW FIELD KEYS FROM %s" % measurement)
        return [(field_key, field_type) for field_key, field_type in iterpoints(rs)]

    async def get_tag_keys(self):
        rs = await self.client.query('SHOW TAG KEYS FROM crds')
        return [tag_key[0] for tag_key in iterpoints(rs)]

    async def make_adhoc_filter(self, filters):
        result = []
        tag_keys = await self.get_tag_keys()
        for filt in filters:
            # Strings for tags which are not regexs must be in single quotes
            if filt['key'] in tag_keys:
                value = filt['value']
                if (isinstance(value, str) and value and value[0] != '/' and value[-1] != '/'):
                    value = "'" + value + "'"
                filt['value'] = value
            result.append('"{key}"{operator}{value}'.format(**filt))
        return ' AND '.join(result).strip()
