import { TimeOption, TimeRange, dateTime, TimeFragment } from '@grafana/data';
import { DataGeneratorPanelProps } from 'types';

export const DEFAULT_TIME_RANGE: TimeRange = {
  from: dateTime().subtract(6, 'h'),
  to: dateTime(),
  raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
};

export const DEFAULT_DATA_GENERATOR_PROPS: DataGeneratorPanelProps = {
  timeRange: DEFAULT_TIME_RANGE,
};

export const DEFAULT_TIME_OPTIONS: TimeOption[] = [
  { from: 'now-5m', to: 'now', display: 'Last 5 minutes', section: 3 },
  { from: 'now-15m', to: 'now', display: 'Last 15 minutes', section: 3 },
  { from: 'now-30m', to: 'now', display: 'Last 30 minutes', section: 3 },
  { from: 'now-1h', to: 'now', display: 'Last 1 hour', section: 3 },
  { from: 'now-3h', to: 'now', display: 'Last 3 hours', section: 3 },
  { from: 'now-6h', to: 'now', display: 'Last 6 hours', section: 3 },
  { from: 'now-12h', to: 'now', display: 'Last 12 hours', section: 3 },
  { from: 'now-24h', to: 'now', display: 'Last 24 hours', section: 3 },
];

export const URL = {
  GET_SAVED_FILES: `http://${window.location.hostname}:8000/grafana_data_generator/api/getsavedfiles`,
  GET_FIELD_KEYS: `http://${window.location.hostname}:8000/grafana_data_generator/api/getkeys`,
  GET_FILE: `http://${window.location.hostname}:8000/grafana_data_generator/api/getfile`,
  GENERATE_FILE: `http://${window.location.hostname}:8000/grafana_data_generator/api/generatefile`,
};
