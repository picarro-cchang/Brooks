import { ReactPanelPlugin } from '@grafana/ui';

import { SimplePanel } from './components/SimplePanel';
import { SimplePanelEditor } from './components/SimplePanelEditor';

import { defaults, SimpleOptions } from './types';

export const reactPanel = new ReactPanelPlugin<SimpleOptions>(SimplePanel);

reactPanel.setEditor(SimplePanelEditor);
reactPanel.setDefaults(defaults);
