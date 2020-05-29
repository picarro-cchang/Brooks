import React from 'react';
import { DataGeneratorPanel } from './../components/DataGeneratorPanel';
import { shallow } from 'enzyme';
import { DataGeneratorPanelProps } from '../types';
import { PanelProps } from '@grafana/ui';
import { LoadingState, TimeFragment, dateTime } from '@grafana/data';
import { DEFAULT_TIME_RANGE } from './../constants/index';

jest.mock('./../services/DataGeneratorService.ts');
jest.mock('./../utils/Notifications.ts');

const defaultProps: PanelProps<DataGeneratorPanelProps> = {
  timeRange: DEFAULT_TIME_RANGE,
  id: 2,
  data: {
    state: LoadingState.Loading,
    series: [],
    timeRange: {
      from: dateTime().subtract(6, 'h'),
      to: dateTime(),
      raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
    },
  },
  timeZone: 'browser',
  options: {
    timeRange: {
      from: dateTime().subtract(6, 'h'),
      to: dateTime(),
      raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
    },
  },
  onOptionsChange: () => {},
  renderCounter: 0,
  transparent: true,
  width: 1692,
  height: 812,
  replaceVariables: (x: string) => {
    return x;
  },
  onChangeTimeRange: () => {},
};
const theme = { theme: 'Grafana Dark' };
describe('<DataGeneratorPanel/>', () => {
  const wrapper = shallow(<DataGeneratorPanel {...defaultProps} {...theme} />);

  it('Create Snapshot', () => {
    expect(wrapper).toMatchSnapshot();
  });
});
