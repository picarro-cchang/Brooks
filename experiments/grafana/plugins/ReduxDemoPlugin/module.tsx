import { PanelPlugin } from '@grafana/ui';
import { CounterPanel } from './src/components/CounterPanel';
import { CounterPanelProps } from './src/components/types';
import { LogService } from './src/services/LogService';

export const plugin = new PanelPlugin<CounterPanelProps>(CounterPanel);

plugin.setDefaults(LogService.getDefaults());
