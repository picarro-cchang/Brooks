import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import {PanelProps} from '@grafana/ui';
import {LogPanel} from '../LogPanel';
import {LogProps} from '../types';

describe('<LogPanel />', () => {
    // const wrapper = shallow(<LogPanel />);
    it('Match Snapshot', () => {
        // expect(wrapper).toMatchSnapshot();
    });
});