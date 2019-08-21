import { PanelPlugin } from '@grafana/ui';
import { LogPanel } from './components/LogPanel';
import { LogPanelEditor } from './components/LogPanelEditor';
import { LogProps } from './components/types';
import { LogService } from '../src/services/LogService';

export const plugin = new PanelPlugin<LogProps>(LogPanel);

plugin.setEditor(LogPanelEditor);
plugin.setDefaults(LogService.getDefaults());
