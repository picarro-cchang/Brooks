import { ReactPanelPlugin } from '@grafana/ui';
import { NetworkPanel } from './components/Network/NetworkPanel';
import { defaults, NetworkOptions } from './types';


export const reactPanel = new ReactPanelPlugin<NetworkOptions>(NetworkPanel);
reactPanel.setDefaults(defaults);
