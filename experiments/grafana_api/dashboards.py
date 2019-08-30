# This depends on installing grafana_api

from grafana_api.grafana_face import GrafanaFace
from grafana_api.grafana_api import GrafanaClientError
import json
import pprint

# We can authenticate either with an API key or using basic authentication

# auth = 'eyJrIjoibzhJYzBBcmJ0UDJtUWhEVEFkVjJUQzZBZllNdkoxS0ciLCJuIjoiTXlBZG1pbktleSIsImlkIjoxfQ=='

auth = ("admin", "admin")
grafana_api = GrafanaFace(auth=auth, host='localhost:3000')

results = grafana_api.search.search_dashboards()
#print(results)

dashboards_by_uid = {}
for result in results:
    dashboards_by_uid[result['uid']] = result['title']

#print(dashboards_by_uid)
# Following code dumps all dashboards into .json files whose names are the dashboard titles
for uid in dashboards_by_uid:
    results = grafana_api.dashboard.get_dashboard(uid)
    title = dashboards_by_uid[uid]
    with open(f"{title}.json", "w") as fp:
        json.dump(results["dashboard"], fp, sort_keys=True, indent=2)
