import { ReactPanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
//import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';

export const reactPanel = new ReactPanelPlugin<ModbusOptions>(ModbusPanel);
//reactPanel.setEditor(ModbusPanelEditor);
reactPanel.setDefaults(defaults);
