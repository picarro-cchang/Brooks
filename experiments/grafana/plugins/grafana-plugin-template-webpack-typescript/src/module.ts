// import { PanelCtrl } from 'grafana/app/plugins/sdk';
//
// class Ctrl extends PanelCtrl {
//
//   static template: string = "<div>Hello from <b>Emma</b></div>";
//
//   constructor($scope, $injector) {
//     super($scope, $injector);
//    }
//
//
//
//   link(scope, element) {
//   }
//
// }
//
// export { Ctrl as PanelCtrl }


import { ReactPanelPlugin } from '@grafana/ui';

import { ModbusPanel } from './components/ModbusPanel';
//import { ModbusPanelEditor } from './components/ModbusPanelEditor';

import { defaults, ModbusOptions } from './types';

export const reactPanel = new ReactPanelPlugin<ModbusOptions>(ModbusPanel);
//reactPanel.setEditor(ModbusPanelEditor);
reactPanel.setDefaults(defaults);
