# This depends on installing grafana_api

from grafana_api.grafana_api import GrafanaAPI
import yaml
import json
from os import getenv


username = getenv('GRAFANA_LOGIN')
passwd = getenv('GRAFANA_PASS')

if username is None or passwd is None:
    raise KeyError('Grafana environmental variables not found!')

ids = []
stream = open("./configuration/app_plugins.yaml", 'r')
dictionary = list(yaml.safe_load_all(stream))
for x in dictionary:
    path = x['path']
    with open(path) as json_file:
        data = json.load(json_file)
        ids.append(data["id"])
# We can authenticate either with an API key or using basic authentication

auth = (username, passwd)
api = GrafanaAPI(auth=auth, host='localhost:3000')

for x in range(0, len(ids)):
    t = api.POST('/plugins/' + str(ids[x]) + '/settings', json={"enabled": False,"pinned": False,"jsonData": None})
    print(t)
