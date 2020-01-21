import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import {LogPanelEditor} from '../LogPanelEditor';
import {LogProps} from '../types';
import {PanelEditorProps} from '@grafana/ui'

const defaultProps: PanelEditorProps<LogProps> = {
    options: {
        level: [],
        limit: 1,
        timeRange: null,
        data: []
    },
    onOptionsChange: () => {},
    data: {
        state: null,
        series: null, 
        timeRange: null
    }
};

describe('<LogPanelEditor />', () => {
    const wrapper = shallow(<LogPanelEditor {...defaultProps}/>);
    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });
});