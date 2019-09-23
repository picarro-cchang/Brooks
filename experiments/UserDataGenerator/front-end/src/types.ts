// @ts-ignore
import { GrafanaTheme } from '@grafana/ui';
import { TimeRange } from '@grafana/data';

export interface DataGeneratorPanelProps {
  timeRange: TimeRange;
  keys: string[];
  fileName: string[];
}

export interface DataGeneratorLayoutProps {
  theme: GrafanaTheme;
  options: DataGeneratorPanelProps;
}
