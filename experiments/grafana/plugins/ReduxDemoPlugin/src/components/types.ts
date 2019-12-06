import { GrafanaTheme } from '@grafana/ui';
import { TimeRange } from '@grafana/data';

export interface CounterPanelProps {
  count: number;
}

export interface CounterProps {
  options: CounterPanelProps;
  theme: GrafanaTheme;
}

export interface CounterComponentProps {
  value: number;
  onIncrement: any;
  onDecrement: any;
}
