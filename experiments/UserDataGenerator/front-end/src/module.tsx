import { PanelPlugin } from '@grafana/ui';
import { DataGeneratorPanel } from './components/DataGeneratorPanel';
import { DataGeneratorPanelProps } from './types';
// import { DataGeneratorService } from './services/DataGeneratorService';

export const plugin = new PanelPlugin<DataGeneratorPanelProps>(DataGeneratorPanel);

// plugin.setDefaults(DataGeneratorService.getDefaults());
