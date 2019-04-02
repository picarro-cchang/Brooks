from flask.views import MethodView
from flask import request


class NetworkRoutes(MethodView):

    def __init__(self, network_obj):
        self.network_obj = network_obj

    def get(self):
        """
        Route to get ip address
        :return:
        """

        # check if request is for rdf data of given id or it is search by criteria
        return self.network_obj.get_ip_address(request)
