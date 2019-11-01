import { PanelPlugin } from '@grafana/ui';
import { SupervisorStatusPanel } from './src/components/SupervisorStatusPanel';
import { SupervisorStatusProps } from './src/types';

export const plugin = new PanelPlugin<SupervisorStatusProps>(SupervisorStatusPanel);

// plugin.setDefaults();
