#!/home/picarro/miniconda3/bin/python3

import json
from grootilities.grootility import GROOTility, gronf

pigss_data_source = {
    "id": 1,
    "orgId": 1,
    "name": "PiGSS data source",
    "type": "influxdb",
    "typeLogoUrl":
    "public/app/plugins/datasource/influxdb/img/influxdb_logo.svg",
    "access": "proxy",
    "url": "http://localhost:8086",
    "password": "",
    "user": "",
    "database": "pigss_data",
    "basicAuth": False,
    "isDefault": True,
    "jsonData": {},
    "readOnly": False
}

port_history_data_source = {
    "id": 2,
    "orgId": 1,
    "name": "port history server",
    "type": "simpod-json-datasource",
    "typeLogoUrl": "public/plugins/simpod-json-datasource/img/json-logo.svg",
    "access": "proxy",
    "url": "http://localhost:8000/port_history/",
    "password": "",
    "user": "",
    "database": "",
    "basicAuth": False,
    "isDefault": False,
    "jsonData": {},
    "readOnly": False
}

telegraf_data_source = {
    "id": 3,
    "orgId": 1,
    "name": "telegraf",
    "type": "influxdb",
    "typeLogoUrl":
    "public/app/plugins/datasource/influxdb/img/influxdb_logo.svg",
    "access": "proxy",
    "url": "http://localhost:8086",
    "password": "",
    "user": "",
    "database": "telegraf",
    "basicAuth": False,
    "isDefault": True,
    "jsonData": {},
    "readOnly": False
}

system_status_data_source = {
    "id": 4,
    "orgId": 1,
    "name": "system status server",
    "type": "simpod-json-datasource",
    "typeLogoUrl": "public/plugins/simpod-json-datasource/img/json-logo.svg",
    "access": "proxy",
    "url": "http://localhost:8000/system_status/",
    "password": "",
    "user": "",
    "database": "",
    "basicAuth": False,
    "isDefault": False,
    "jsonData": {},
    "readOnly": False
}

species_type_data_source = {
    "id": 4,
    "orgId": 1,
    "name": "species type service",
    "type": "simpod-json-datasource",
    "typeLogoUrl": "public/plugins/simpod-json-datasource/img/json-logo.svg",
    "access": "proxy",
    "url": "http://localhost:8000/species/",
    "password": "",
    "user": "",
    "database": "",
    "basicAuth": False,
    "isDefault": False,
    "jsonData": {},
    "readOnly": False
}

# TODO: Improve grootilities to not rely on a list of app ids for production
apps = [
    'picarro-analyzer-page', 'current-concentration-values',
    'picarro-user-data-app', 'picarro-concentration-page',
    'picarro-status-app', '1flow-setup-app'
]


def main():
    with GROOTility('production') as GROOT:
        # TODO: Handle provisioning existing datasources without throwing warning
        print(f'Provisioning datasources')
        GROOT.add_datasource(pigss_data_source)
        GROOT.add_datasource(port_history_data_source)
        GROOT.add_datasource(telegraf_data_source)
        GROOT.add_datasource(system_status_data_source)
        GROOT.add_datasource(species_type_data_source)
        # TODO: Improve grootilities to not rely on a list of app ids for production
        for app in apps:
            print(f'Provisioning: {app}')
            GROOT.api.POST(f'/plugins/{app}/settings',
                           json={
                               "enabled": False,
                               "pinned": False,
                               "jsonData": None
                           })
            GROOT.api.POST(f'/plugins/{app}/settings',
                           json={
                               "enabled": True,
                               "pinned": True,
                               "jsonData": None
                           })
        # Fetch all of the existing users and create a default viewer
        # user if necessary.S
        users_api = GROOT.api.GET(f'/users?')
        user_list = []
        for user in users_api:
            user_list.append(user['login'])
        if not 'viewer' in user_list:
            GROOT.add_user('viewer', 'viewer', 'viewer@localhost', 'viewer')


if __name__ == '__main__':
    main()
