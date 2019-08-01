# This depends on installing grafana_api

from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_api import GrafanaClientError

# We can authenticate either with an API key or using basic authentication

# auth = 'eyJrIjoibzhJYzBBcmJ0UDJtUWhEVEFkVjJUQzZBZllNdkoxS0ciLCJuIjoiTXlBZG1pbktleSIsImlkIjoxfQ=='

auth = ("admin", "admin")
grafana_api = GrafanaFace(auth=auth, host='localhost:3000')

result = grafana_api.search.search_dashboards(tag='pigss')
print(result)

ds_name = "test_datasource"

# Create a test datasource
sample_ds = {
  "name": ds_name,
  "type": "influxdb",
  "url": "http://localhost:8086",
  "database": "pigss_data",
  "access": "proxy",
  "basicAuth": False
}

try:
    print(grafana_api.datasource.find_datasource(ds_name))
except GrafanaClientError:
    print("Datasource does not exist - Creating")
    print(grafana_api.datasource.create_datasource(sample_ds))    
else:
    print("Datasource already exists")


result = grafana_api.datasource.list_datasources()
print(result)

print("Deleting datasource")
result = grafana_api.datasource.delete_datasource_by_name(ds_name)
print(result)
