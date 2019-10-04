#!/usr/bin/python3
#
# FILE:
#   aio_influx_database.py
#
# DESCRIPTION:
#   Access influx database via asynchronous coroutines
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   3-Oct-2019  sze  Initial check-in from experiments
#
#  Copyright (c) 2008-2019 Picarro, Inc. All rights reserved
#
import asyncio
import datetime
import os

from aioinflux import InfluxDBClient, iterpoints
from back_end.database_access.conf import database_name, port, server

FILE_NAME = os.path.abspath(__file__)


class AioInfluxDBWriter:
    def __init__(self, address=None, db_port=None, db_name=None):
        self.address = address if address is not None else server
        self.db_port = db_port if db_port is not None else port
        self.db_name = db_name if db_name is not None else database_name

        self._client = InfluxDBClient(host=self.address, port=self.db_port, database=self.db_name)

    async def ensure_database_present(self):
        if self.db_name not in await self._client.query("SHOW DATABASES"):
            await self._client.query(f"CREATE DATABASE {self.db_name}")

    async def write_data(self, data_dict):
        """
        Write dictionary data
        :param data_dict:
        :return:
        """
        await self.ensure_database_present()
        if not isinstance(data_dict, list):
            raise TypeError(FILE_NAME, ": input data is not dictionary type")
        await self._client.write(data_dict)

    async def read_data(self, query, **args):
        await self.ensure_database_present()
        return await self._client.query(query)

    async def close_connection(self):
        await self._client.close()

    def get_db_address(self):
        return self.address

    def get_db_port(self):
        return self.db_port

    def get_db_name(self):
        return self.db_name


def create_dict(measurement, fields, tags=None):
    if not isinstance(measurement, str):
        raise ValueError("measurement must be string")
    if tags is None:
        tags = {}
    if not isinstance(tags, dict):
        raise ValueError("tags must be dictionary")
    if not isinstance(fields, dict):
        raise ValueError("fields must be dictionary")
    return {"measurement": measurement, "tags": tags, "fields": fields}


if __name__ == "__main__":

    async def main():
        db_Writer = AioInfluxDBWriter()
        data = [{
            "measurement": "modbusSettings",
            "tags": {},
            "fields": {
                "sslave": 4,
                "port": 505
            },
            "time": datetime.datetime.now()
        }]
        await db_Writer.write_data(data)
        data = await db_Writer.read_data("select * from modbusSettings ")
        print(list(iterpoints(data)))

    asyncio.run(main())
