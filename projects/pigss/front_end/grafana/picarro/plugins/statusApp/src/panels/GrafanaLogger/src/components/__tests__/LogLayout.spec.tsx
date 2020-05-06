import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import {LogLayout} from '../LogLayout';
import {LogSectionProps} from '../types'
const defaultProps: LogSectionProps = {
    options: {
        level: [],
        limit: 1,
        timeRange: null,
        data: []
    },
    theme: null
};
describe('<LogLayout />', () => {
    const wrapper = shallow(<LogLayout {...defaultProps}/>);
    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });
});
