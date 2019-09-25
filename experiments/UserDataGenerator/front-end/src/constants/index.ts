// @ts-ignore
import { TimeOption, TimeRange, dateTime, TimeFragment } from '@grafana/data';
// import { DataGeneratorPanelProps } from 'types';

export const DEFAULT_TIME_RANGE: TimeRange = {
  from: dateTime(),
  to: dateTime(),
  raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
};

// const DEFAULT_KEYS: string[] = ['A', 'B', 'C'];

// export const DEFAULT_DATA_GENERATOR_PROPS: DataGeneratorPanelProps = {
//   timeRange: DEFAULT_TIME_RANGE,
//   keys: DEFAULT_KEYS,
//   fileName: [
//     "09-12-2019 CO2 H20 NH3 Picarro.txt",
//     "09-13-2019 CO2 H20 NH3 Picarro.txt",
//     "09-14-2019 CO2 H20 NH3 Picarro.txt"]
// };

export const KEYS_OPTIONS = [
  { value: 'H2O', label: 'H2O' },
  { value: 'CO2', label: 'CO2' },
  { value: 'NH3', label: 'NH3' },
  { value: 'CH4', label: 'CH4' },
  { value: 'HF', label: 'HF' },
  { value: 'HC', label: 'HC' },
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
  GET_SAVED_FILES: "http://localhost:8010/api/getsavedfiles",
  GET_FILE: "http://localhost:8010/api/getfile"
}