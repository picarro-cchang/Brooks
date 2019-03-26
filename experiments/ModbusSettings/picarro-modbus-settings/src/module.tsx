import { ReactPanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';

let local = { ...defaults };
var request = require('sync-request');

// Get user information
var res = request('GET', 'http://localhost:3000/api/user');
if (res.statusCode == 200) {
  var json = JSON.parse(res.getBody());
  local['user'] = json;
} else {
  console.log('Network GET request failed for current user');
  throw Error('Network GET request failed for current user');
}

// lets get organization information of user
var url = 'http://localhost:3000/api/users/';
url += local['user']['id'];
url += '/orgs';
var auth = 'Basic ' + new Buffer('admin:admin').toString('base64');
res = request('GET', url, {
  headers: {
    Authorization: auth,
  },
});
if (res.statusCode == 200) {
  var json = JSON.parse(res.getBody());
  local['UserOrgInfo'] = json[0];
  console.log(local['UserInfo']);
} else {
  console.log('Network GET request failed for current user role');
  throw Error('Network GET request failed for current user role');
}

// get current modbus settings from middle tier
res = request('GET', 'http://localhost:4000/modbus_settings');
if (res.statusCode == 200) {
  var json = JSON.parse(res.getBody());
  local['slaveId'] = parseInt(json['slave']);
  local['tcpPort'] = parseInt(json['port']);
} else {
  console.log('Network GET request failed for modbus settings');
  throw Error('Network GET request failed for modbus settings');
}

export const reactPanel = new ReactPanelPlugin<ModbusOptions>(ModbusPanel);
// lets dont give modification functionality if user is not admin
if (local['UserOrgInfo']['role'] === 'Admin') {
  reactPanel.setEditor(ModbusPanelEditor);
}
reactPanel.setDefaults(local);
