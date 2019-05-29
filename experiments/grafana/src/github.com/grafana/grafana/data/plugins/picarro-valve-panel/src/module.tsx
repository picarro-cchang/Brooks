import { ReactPanelPlugin } from '@grafana/ui';
import store from './store';
import { getValveMode } from './actions/valveActions';

import ValvePanel from './components/ValvePanel';
import { ValvePanelEditor } from './components/ValvePanelEditor';

import { defaults, ValvePanelOptions } from './types';

export const reactPanel = new ReactPanelPlugin<ValvePanelOptions>(ValvePanel);

reactPanel.setEditor(ValvePanelEditor);
reactPanel.setDefaults(defaults);

setInterval(() => {
  store.dispatch(getValveMode());
}, 5000);
