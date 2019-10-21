import { PanelPlugin } from '@grafana/ui';
import { LogPanel } from './src/components/LogPanel';
import { LogPanelEditor } from './src/components/LogPanelEditor';
import { LogProps } from './src/components/types';
import { LogService } from './src/services/LogService';

export const plugin = new PanelPlugin<LogProps>(LogPanel);

plugin.setEditor(LogPanelEditor);
plugin.setDefaults(LogService.getDefaults());
