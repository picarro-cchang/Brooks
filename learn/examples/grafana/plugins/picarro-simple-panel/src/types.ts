import {
  GrafanaTheme,
  TimeRange,
//  TimeSeriesVMs,
} from '@grafana/ui';

export interface SimpleOptions {
  maxValue: number;
  minValue: number;
  textValue: string;
};

export const defaults: SimpleOptions = {
  minValue: 0,
  maxValue: 100,
  textValue: "Sample string",
};

export interface LayoutProps {
//  timeSeries: TimeSeriesVMs;
  timeRange: TimeRange;
  width: number;
  height: number;
  options: SimpleOptions;
  theme: GrafanaTheme;
  onInterpolate: (value: string, format?: string) => string;
};
