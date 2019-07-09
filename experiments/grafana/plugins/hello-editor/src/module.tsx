import { ReactPanelPlugin } from '@grafana/ui';
import { HelloPanel } from './components/Hello/HelloPanel';
import { HelloPanelEditor } from './components/Hello/HelloPanelEditor';

import { defaults, HelloOptions } from './types';

export const reactPanel = new ReactPanelPlugin<HelloOptions>(HelloPanel);

reactPanel.setEditor(HelloPanelEditor);
reactPanel.setDefaults(defaults);
