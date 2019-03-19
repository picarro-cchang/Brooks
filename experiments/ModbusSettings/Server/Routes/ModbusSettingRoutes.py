from flask.views import MethodView
from flask import request


class ModbusSettingsRoutes(MethodView):

    def __init__(self, modbus_settings_obj):
        self.modbus_settings_obj = modbus_settings_obj

    def get(self):
        """
        Routs to get modbus settings
        :return:
        """

        # get modbus settings
        return self.modbus_settings_obj.get_modbus_settings(request)


    def post(self):
        """
        Routs to save modbus settings
        :return:
        """
        # set modbus settings
        return self.modbus_settings_obj.set_modbus_settings(request)
