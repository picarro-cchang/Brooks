// import { ReactPanelPlugin } from '@grafana/ui';
import { PanelPlugin } from '@grafana/ui';
import store from './store';
import { getValveMode } from './actions/valveActions';

import ValvePanel from './components/ValvePanel';
import { ValvePanelEditor } from './components/ValvePanelEditor';

import { defaults, ValvePanelOptions } from './types';

export const plugin = new PanelPlugin<ValvePanelOptions>(ValvePanel);

plugin.setEditor(ValvePanelEditor);
plugin.setDefaults(defaults);

setInterval(() => {
  store.dispatch(getValveMode());
}, 5000);
