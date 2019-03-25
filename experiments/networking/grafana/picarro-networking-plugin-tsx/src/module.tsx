import { ReactPanelPlugin } from '@grafana/ui';
import { NetworkPanel } from './components/Network/NetworkPanel';
import { NetworkPanelEditor } from './components/Network/NetworkPanelEditor';

import { defaults, NetworkOptions } from './types';

export const reactPanel = new ReactPanelPlugin<NetworkOptions>(NetworkPanel);

reactPanel.setEditor(NetworkPanelEditor);
reactPanel.setDefaults(defaults);
