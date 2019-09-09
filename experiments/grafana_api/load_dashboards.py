# This depends on installing grafana_api

from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_api import GrafanaClientError
import json
import pprint

from glob import glob

# We can authenticate either with an API key or using basic authentication
# auth = 'eyJrIjoibzhJYzBBcmJ0UDJtUWhEVEFkVjJUQzZBZllNdkoxS0ciLCJuIjoiTXlBZG1pbktleSIsImlkIjoxfQ=='

auth = ("admin", "admin")
grafana_api = GrafanaFace(auth=auth, host='localhost:3000')

# Delete all existing dashboards
results = grafana_api.search.search_dashboards()
for result in results:
    print(f"Deleting dashboard {result['title']}")
    uid = result['uid']
    grafana_api.dashboard.delete_dashboard(uid)

# Load all .json files as dashboards
for filename in glob("*.json"):
    with open(filename, "r") as fp:
        dashboard = json.load(fp)
        dashboard["id"] = None  # Indicate we want to create this dashboard
        result = grafana_api.dashboard.update_dashboard({
            "dashboard": dashboard,
            "folderId": 0
        })
        print(result)
