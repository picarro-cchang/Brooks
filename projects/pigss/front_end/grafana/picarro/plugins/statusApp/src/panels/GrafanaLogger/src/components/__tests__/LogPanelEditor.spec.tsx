import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import {LogPanelEditor} from '../LogPanelEditor';
import {LogProps} from '../types';
import {PanelEditorProps} from '@grafana/ui'

const onOptionsMock = jest.fn();
const defaultProps: PanelEditorProps<LogProps> = {
    options: {
        level: [{ value: '10', label: '10' }],
        limit: 1,
        timeRange: null,
        data: [[]]
    },
    onOptionsChange: onOptionsMock,
    data: {
        state: null,
        series: null, 
        timeRange: null
    }
};

describe('<LogPanelEditor />', () => {
    const wrapper = shallow(<LogPanelEditor {...defaultProps}/>);
    const instance = wrapper.instance() as LogPanelEditor;

    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('onLevelChange', () => {
        instance.onLevelChange([{ value: '10', label: '10' }]);
        expect(onOptionsMock).toHaveBeenCalled();
    });

    it('onLimitChange', () => {
        instance.onLimitChange(20);
        expect(onOptionsMock).toHaveBeenCalled();
    });
});
