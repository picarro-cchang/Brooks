from flask import request, jsonify
from flask_restplus import Resource, Api, reqparse

from models.log import EventsModel


class Log(Resource):
    def get(self):
        query = EventsModel.build_query(request.args)
        logs = EventsModel.execute_query(query)
        return jsonify(logs)
