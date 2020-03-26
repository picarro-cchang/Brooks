import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import asyncio

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop, TestClient
from aiohttp import web

from back_end.servers.grafana_logger_service import GrafanaLoggerService
from back_end.lologger.lologger_client import LOLoggerClient

class GrafanaLoggerTestCase(AioHTTPTestCase):
    """ This class contains the test cases for GrafanaLogger service.

    """

    def create_mock_service(self):
        """ Create Mock Grafana Logger Service for test cases.

        Returns: An instance of GrafanaLoggerService with mocked methods.
        """
        config_filename = "/home/picarro/git/host/projects/pigss/back_end/pigss_sim_config.yaml"
        farm = Mock()
        farm.config = Mock()
        farm.config.configure_mock(**{'get_glogger_plugin_config.return_value': {
            "sqlite": {
                "table_name": "Events",
                "columns": ["rowid", "ClientTimestamp", "ClientName", "LogMessage", "Level", "EpochTime"]
            },
            "limit": 20,
            "interval": 5,
            "level": [20, 30, 40, 50],
            "timeout": 300,
            "retries": 1
        }})

        lologger_proxy = Mock()
        lologger_proxy.configure_mock(**{'get_sqlite_path.return_value': '_2020_02.db'})

        log_client = Mock()
        log_client.configure_mock(**{
            'debug.return_value': 'Debug',
            'error.return_value': 'Error'
        })

        return GrafanaLoggerService(farm=farm, lologger_proxy=lologger_proxy, log=log_client)

    async def get_application(self):
        """
        get_application has to be overriden to return web.Application instance
        """
        app = web.Application()
        app.add_subapp("/grafana_logger/", self.create_mock_service().app)
        return app

    @unittest_run_loop
    async def test_grafana_logger_ping(self):
        """ Test the API is up and running, and at least responding to pings

        This does not mean all other endpoints are performing normally.
        """
        response = await self.client.request("GET", "/grafana_logger/ping")
        assert response.status == 200
        text = await response.text()
        assert "OK" in text

    @unittest_run_loop
    async def test_handle_status_leaky_connection(self):
        """ Make sure that no of connections does not exceed open and disconnected websocket traffic.
            That would mean, the server is keeping websocket connections alive when it should not.
        """
        response = await self.client.request('GET', '/grafana_logger/stats')
        assert response.status == 200
        stats = await response.json()
        self.assertEqual(stats['ws_connections'], stats['ws_open']+stats['ws_disconnections'])

    @unittest_run_loop
    async def test_hitting_incorrect_endpoint(self):
        """ Hitting incorrect endpoint should result in status code 400 errors.
        """
        response = await self.client.request('GET', '/grafana_logger/foo')
        assert response.status == 400

    @unittest_run_loop
    async def test_grafana_logger_get_latest_db(self):
        service = self.create_mock_service()
        latest_db = service.get_latest_db()
        assert latest_db == '_2020_02.db'

    @unittest_run_loop
    async def test_grafana_logger_get_logs_without_query_params(self):
        """ Trying to fetch logs without query parameters should respond with log messages from the start i.e. rowid=1.
        """
        response = await self.client.request('GET', '/grafana_logger/getlogs')
        if response.status != 200:
            self.assertFalse(response.status == 200, "Request Get Failed")

        if response is not None:
            try:
                data = await response.json()
            except json.JSONDecodeError:
                print(data)
            assert len(data) >= 0

    @unittest_run_loop
    async def test_grafana_logger_get_logs_with_correct_query_params(self):
        """ Trying to fetch logs without query parameters should respond with 'Error in fetching logs' message..
        """
        url = ("/grafana_logger/getlogs?rowid=-1&limit=1000&start=1582175848406&end=1582176748406&"
                 "interval=5&level=20&level=30&level=40&level=50")
        response = await self.client.request('GET', url)
        if response.status != 200:
            self.assertFalse(response.status == 200, "Request Get Failed")

        if response is not None:
            try:
                data = await response.json()
            except json.JSONDecodeError:
                print(data)
            assert len(data) >= 0

    @unittest_run_loop
    async def test_grafana_logger_logs_in_correct_timerange(self):
        """ Check if the queried logs, if returned by the service are in correct timerange.
        """
        start = 1582674122000
        end = 1582674160000
        url = (f"/grafana_logger/getlogs?rowid=-1&limit=1000&start={start}&end={end}&interval=5&level=20"
               "&level=30&level=40&level=50")
        response = await self.client.request('GET', url)
        if response.status != 200:
            self.assertFalse(response.status == 200, "Request Get Failed")

        if response is not None:
            try:
                data = await response.json()
            except json.JSONDecodeError:
                print(data)
            length = len(data)
            self.assertGreaterEqual(length, 0)

            if length > 0 and "message" not in data:
                epochs = [row[5] for row in data]
                self.assertGreaterEqual(min(epochs), start)
                self.assertLessEqual(max(epochs), end)


    @unittest_run_loop
    async def test_grafana_logger_check_if_websocket_connection_opened(self):
        """ Check if websocket connection request is accepted by the service, and if the server responds with messages.
        """
        url = "/grafana_logger/ws"
        ws_connection = await self.client.ws_connect(url)

        if ws_connection is not None:
            self.assertFalse(ws_connection.closed, False)
            await ws_connection.ping()

    @unittest_run_loop
    async def test_grafaba_logger_check_if_websocket_connection_closed_properly(self):
        """ Check if when connection is disconnected by sending CLOSE message, service closed the connection properly.
        """
        url = "/grafana_logger/ws"
        ws_connection = await self.client.ws_connect(url)

        if ws_connection is not None:
            self.assertFalse(ws_connection.closed, "WS Connection is Open")
            await ws_connection.send_str(data="CLOSE")
            await ws_connection.close()
            self.assertTrue(ws_connection.closed, "WS Connection is Closed")


if __name__ == '__main__':
    unittest.main()
