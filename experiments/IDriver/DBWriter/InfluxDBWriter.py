from influxdb import InfluxDBClient
from .conf import server, port, database_name
from .IWriter import IWriter

FILE_NAME = "DBWriter/InfluxDBWriter.py"


# lets say our class is implementing IWriter interface
@IWriter.register
class InfluxDBWriter:
    def __init__(self, address=None, db_port=None, db_name=None):
        self.address = address if address is not None else server
        self.db_port = db_port if db_port is not None else port
        self.db_name = db_name if db_name is not None else database_name

        self._client = InfluxDBClient(host=self.address, port=self.db_port)
        if self.db_name not in self._client.get_list_database():
            self._client.create_database(self.db_name)
        self._client.switch_database(self.db_name)

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
    return {
        "measurement": measurement,
        "tags": tags,
        "fields": fields}

if __name__ == "__main__":
    db_Writer = InfluxDBWriter()
    data = [{
        "measurement": "modbusSettings",
        "tags": {},
        "fields": {"sslave": 4, "port": 505}
    }]
    db_Writer.write_data(data)
    data = db_Writer.read_data("select * from modbusSettings ")
    print(list(data.get_points()))