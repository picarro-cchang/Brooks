// @ts-ignore
import { PanelPlugin } from '@grafana/ui';
import { HelloPanel } from './components/Hello/HelloPanel';
import { HelloPanelEditor } from './components/Hello/HelloPanelEditor';

import { defaults, HelloOptions } from './types';

export const plugin = new PanelPlugin<HelloOptions>(HelloPanel);

plugin.setEditor(HelloPanelEditor);
plugin.setDefaults(defaults);
