import json
import socket


class ModbusSettingModule:

    def get_modbus_settings(self, req):
        """
        Method use to get modbus settings
        :return:
        """
        try:
            modbus_settings = {'slave': '2', 'port': '505'}
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
            data = json.dumps(req.json)
            print(data)
            return json.dumps({"message": "success"}), 200
        except Exception as ex:
            # if exception catch reply with error
            return json.dumps({"message": str(ex)}), 400
