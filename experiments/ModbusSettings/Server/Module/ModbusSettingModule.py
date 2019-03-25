import json
import socket
from host.experiments.DBDriver.IWriter import IWriter


class ModbusSettingModule:

    def __init__(self, writer):
        # check if writer is type of Iwriter if not raise exception
        if not isinstance(writer, IWriter):
            raise TypeError('Expected connection object of IWriter ')
        self._writer = writer


    def get_modbus_settings(self, req):
        """
        Method use to get modbus settings
        :return:
        """
        try:
            data = self._writer.read_data("select port,slave from modbusSettings ORDER BY time DESC LIMIT 1")
            modbus_settings= list(data.get_points())[0]
            print(modbus_settings)
            # send response
            return json.dumps(modbus_settings), 200
        except Exception as ex:
            # if exception catch reply with error
            return json.dumps({"message": str(ex)}), 400

    def set_modbus_settings(self, req):
        """
        Method use to save modbus settings when user configure it
        :param req:
        :return:
        """
        try:
            data = req.json
            print(data)
            write_data = [{
                "measurement": "modbusSettings",
                "fields": {
                    "slave": int(data['slave']),
                    "port": int(data['port']),
                    "user":data['user']
                }
            }]
            print(write_data)
            self._writer.write_data(write_data)
            return json.dumps({"message": "success"}), 200
        except Exception as ex:
            # if exception catch reply with error
            return json.dumps({"message": str(ex)}), 400
