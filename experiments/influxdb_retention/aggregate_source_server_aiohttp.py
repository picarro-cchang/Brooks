import asyncio
import time

import aiohttp
import aiohttp_cors
import attr
from aiohttp import web
from aiohttp_swagger import setup_swagger

from calendar import timegm
from collections import namedtuple
from datetime import datetime
from aioinflux import InfluxDBClient, iterpoints


@attr.s
class HttpHandlers:
    app = attr.ib(None)
    runner = attr.ib(None)
    tasks = attr.ib(factory=list)
    client = attr.ib(None)
    durations = attr.ib(factory=lambda: ["15s", "1m", "5m", "15m", "1h", "4h", "12h", "24h"])
    durations_ms = attr.ib(
        factory=lambda: [15000, 1 * 60000, 5 * 60000, 15 * 60000, 1 * 3600000, 4 * 3600000, 12 * 3600000, 24 * 3600000])

    async def health_check(self, request):
        return web.Response(text='This datasource is healthy.')

    async def search(self, request):
        """
        ---
        description: Returns field names in the crds measurement

        tags:
            -   Grafana JSON source from InfluxDB
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
            -   Grafana JSON source from InfluxDB
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
            -   Grafana JSON source from InfluxDB
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
            -   Grafana JSON source from InfluxDB
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
            for which, duration_ms in enumerate(self.durations_ms):
                if range_ms < max_data_points * duration_ms:
                    break
            # which is probably best, but check all coarser resolutions in case one
            #  has data closer to the starting time

            # Candidates contains tuples with (|start_time_ofset|, duration_ms, duration, data_points)
            #  when these are sorted into ascending order, the first entry with data_points < max_data_points
            #  is the one we use

            Candidate = namedtuple("Candidate", ['start_time_offset', 'duration_ms', 'duration', 'data_points'])
            candidates = []
            for duration, duration_ms in zip(self.durations[which:], self.durations_ms[which:]):
                rs = await self.client.query(
                    f'SELECT "mean_{target}" FROM crds_{duration} '
                    f'WHERE {where_clause} time>={start_time_ms}ms AND time<{stop_time_ms}ms ORDER BY time ASC LIMIT 1',
                    epoch='ms')
                times = [result[0] for result in iterpoints(rs)]
                if times:
                    candidates.append(Candidate(abs(times[0] - start_time_ms), duration_ms, duration, range_ms // duration_ms))
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
                    candidates.append(Candidate(abs(times[0] - start_time_ms), 0, '0', counts[0] // 2))
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
                    f' FROM crds_{best_duration} WHERE {where_clause} time>={start_time_ms-duration_ms}ms AND time<{stop_time_ms+duration_ms}ms)'
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

    async def server_init(self, port):
        self.client = InfluxDBClient(host='localhost', port=8086, db='pigss_sim_data')  # Host/Port for InfluxDB
        app = web.Application()
        self.app = app
        app.on_shutdown.append(self.on_shutdown)
        cors = aiohttp_cors.setup(
            app, defaults={"*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )})

        app.add_routes([
            web.get('/', self.health_check),
            web.get('/search', self.search),
            web.post('/search', self.search),
            web.get('/tag-keys', self.tag_keys),
            web.post('/tag-keys', self.tag_keys),
            web.post('/tag-values', self.tag_values),
            web.post('/query', self.query)
        ])
        setup_swagger(app)

        for route in app.router.routes():
            cors.add(route)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', port)
        await site.start()
        return app

    async def on_shutdown(self, app):
        return

    async def shutdown(self):
        for task in self.tasks:
            task.cancel()
        await self.app.shutdown()
        await self.app.cleanup()
        await self.runner.cleanup()

    async def startup(self):
        self.tasks.append(asyncio.create_task(self.server_init(5000)))


if __name__ == "__main__":
    handlers = HttpHandlers()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handlers.startup())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.run_until_complete(handlers.shutdown())
        loop.close()
    print('Stop server end')
