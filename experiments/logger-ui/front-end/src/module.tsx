import { PanelPlugin } from '@grafana/ui';
import { TablePanel } from './components/DataTable/TablePanel';
import { TablePanelEditor } from './components/DataTable/TablePanelEditor';
import { TableOptions } from './components/DataTable/types';
import { LogService } from '../src/services/LogService';

export const plugin = new PanelPlugin<TableOptions>(TablePanel);

plugin.setEditor(TablePanelEditor);
plugin.setDefaults(LogService.getDefaults());
