import { PanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
//import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';

export const plugin = new PanelPlugin<ModbusOptions>(ModbusPanel);
//reactPanel.setEditor(ModbusPanelEditor);
plugin.setDefaults(defaults);
