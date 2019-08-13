import { PanelPlugin } from '@grafana/ui';
import { NetworkPanel} from "./components/NetworkPanel";
import { defaults, NetworkOptions } from './types';
import {NetworkPanelEditor} from "./components/NetworkPanelEditor";


export const plugin = new PanelPlugin<NetworkOptions>(NetworkPanel);
plugin.setEditor(NetworkPanelEditor);
plugin.setDefaults(defaults);
