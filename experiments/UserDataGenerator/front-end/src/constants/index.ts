// @ts-ignore
import { TimeOption, TimeRange, dateTime, TimeFragment } from '@grafana/data';
import { DataGeneratorPanelProps } from 'types';

console.log('dateTime here', dateTime());

export const DEFAULT_TIME_RANGE: TimeRange = {
  from: dateTime().subtract(6, "h"),
  to: dateTime(),
  raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
};

export const DEFAULT_DATA_GENERATOR_PROPS: DataGeneratorPanelProps = {
  timeRange: DEFAULT_TIME_RANGE,
};

export const KEYS_OPTIONS = [
  { value: 'H2O', label: 'H2O' },
  { value: 'CO2', label: 'CO2' },
  { value: 'NH3', label: 'NH3' },
  { value: 'CH4', label: 'CH4' },
  { value: 'HF', label: 'HF' },
  { value: 'HCl', label: 'HCl' },
];

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
  GET_SAVED_FILES: 'http://localhost:8010/api/getsavedfiles',
  GET_FIELD_KEYS: 'http://localhost:8010/api/getkeys',
  GET_FILE: 'http://localhost:8010/api/getfile',
  GENERATE_FILE: 'http://localhost:8010/api/generatefile',
};
