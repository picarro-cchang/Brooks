from grafana_api.grafana_api import GrafanaAPI

auth = ("admin", "admin")
api = GrafanaAPI(auth, host='localhost:3000')
r = api.POST('/auth/keys', json={"role": "Admin", "name": "new_api_key"})
print(r)
r = api.GET('/auth/keys')
print(r)
