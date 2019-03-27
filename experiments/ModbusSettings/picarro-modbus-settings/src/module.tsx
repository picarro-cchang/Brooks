import { ReactPanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';

let local = { ...defaults };
var request = require('sync-request');

// get current modbus settings from middle tier
var res = request('GET', 'http://localhost:4000/modbus_settings');
if (res.statusCode == 200) {
  var json = JSON.parse(res.getBody());
  local['slaveId'] = parseInt(json['slave']);
  local['tcpPort'] = parseInt(json['port']);
} else {
  console.log('Network GET request failed for modbus settings');
  throw Error('Network GET request failed for modbus settings');
}
console.log(local);
export const reactPanel = new ReactPanelPlugin<ModbusOptions>(ModbusPanel);
reactPanel.setEditor(ModbusPanelEditor);
reactPanel.setDefaults(local);
