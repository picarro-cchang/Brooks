
import datetime
import time
from influxdb import InfluxDBClient
from host.experiments.DBDriver.conf import server, port, database_name
from host.experiments.DBDriver.IWriter import IWriter

FILE_NAME = "DBDriver/InfluxDBWriter.py"


class InfluxDBWriter(IWriter):
    def __init__(self, address=None, db_port=None, db_name=None):
        if address is None:
            address = server
        if db_port is None:
            db_port = port
        if db_name is None:
            db_name = database_name
        self._client = InfluxDBClient(host=address, port=db_port)
        if db_name not in self._client.get_list_database():
            self._client.create_database(db_name)
        self._client.switch_database(db_name)

    def write_data(self, data_dict):
        """
        Write dictionary data
        :param data_dict:
        :return:
        """
        if not isinstance(data_dict, list):
            raise TypeError(FILE_NAME, ": input data is not dictionary type")
        self._client.write_points(data_dict)

    def read_data(self, query, **args):
        return self._client.query(query)

    def close_connection(self):
        self._client.close()


# lets say our class is implementing IWriter interface
#IWriter.register(InfluxDBClient)

if __name__ == "__main__":
    db_Writer = InfluxDBWriter()
    data = [{
        "measurement": "modbusSettings",
        "tags": {},
        "fields": {"slave": 4, "port": 505}
    }]
    #db_Writer.write_data(data)
    data = db_Writer.read_data("select port,slave from modbusSettings ORDER BY time DESC LIMIT 1")
    print(list(data.get_points())[0])
