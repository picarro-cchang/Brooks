import { ReactPanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';
import PicarroAPI from './api/PicarroAPI';

export const reactPanel = new ReactPanelPlugin<ModbusOptions>(ModbusPanel);
console.log(defaults);

PicarroAPI.getRequest('http://localhost:4000/modbus_settings').then(
  response => {
    console.log(defaults);
    let localValues = { ...defaults };
    localValues['slaveId'] = parseInt(response['slave']);
    localValues['tcpPort'] = parseInt(response['port']);
    reactPanel.setEditor(ModbusPanelEditor);
    reactPanel.setDefaults(localValues);
  }
);
