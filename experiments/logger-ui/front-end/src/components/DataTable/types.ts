import { GrafanaTheme } from '@grafana/ui';
import { TimeRange } from '@grafana/data';

export interface TableOptions {
  thead: string[];
  level: string;
  limit: number;
  date: TimeRange;
}

export interface TableProps {
  options: TableOptions;
  theme: GrafanaTheme;
}

export interface CellType {
  data: string[];
}
