import { GrafanaTheme } from '@grafana/ui';
import { TimeRange } from '@grafana/data';

export interface LogProps {
  level: string;
  limit: number;
  date: TimeRange;
  data: string[][];
}

export interface LogSectionProps {
  options: LogProps;
  theme: GrafanaTheme;
}

export interface CellProps {
  row: string[];
}
