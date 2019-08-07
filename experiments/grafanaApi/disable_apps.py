# This depends on installing grafana_api

from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_api import GrafanaAPI
import json
import pprint

# We can authenticate either with an API key or using basic authentication

# auth = 'eyJrIjoibzhJYzBBcmJ0UDJtUWhEVEFkVjJUQzZBZllNdkoxS0ciLCJuIjoiTXlBZG1pbktleSIsImlkIjoxfQ=='

auth = ("picarro", "picarro")
api = GrafanaAPI(auth=auth, host='localhost:3000')
#req = {"enabled":true,"pinned":true,"jsonData":null}
path1 = '/plugins/picarro-concentration-page/settings'
path1 = '/plugins/multi-app/settings'
path1 = '/plugins/picarro-analyzer-page/settings'
path1 = '/plugins/settings-app/settings'
path1 = '/plugins/picarro-summary-page/settings'

t = api.POST(path, json={"enabled": True,"pinned": True,"jsonData": None})
print(t)