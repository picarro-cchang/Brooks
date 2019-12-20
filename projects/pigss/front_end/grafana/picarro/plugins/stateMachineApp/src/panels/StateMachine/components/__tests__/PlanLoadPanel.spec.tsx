import React, { ReactText } from 'react';
import Modal from 'react-responsive-modal';
import { shallow, mount, render } from 'enzyme';
import WS from 'jest-websocket-mock';
import 'jest-styled-components';
import PlanLoadPanel from '../PlanLoadPanel';
import { PlanLoadPanelOptions } from '../../types';

const mockClick = jest.fn();
const mockUpdateFileName = jest.fn();
const defaultProps: PlanLoadPanelOptions = {
    plan: {
        max_steps: 32,
        panel_to_show: 3,
        current_step: 1,
        focus: {
            row: 1,
            column: 2
        },
        last_step: 1,
        steps: {
            "1": {
                "banks": {
                    "1": {
                    "clean": 0,
                    "chan_mask": 1
                    },
                    "2": {
                    "clean": 0,
                    "chan_mask": 0
                    }
                },
                "reference": 0,
                "duration": 30
            }
        },
        num_plan_files: 1,
        plan_filename: "test.pln",
        plan_files: {
            "1": "test.pln"
        },
        bank_names: {
            "1": {
                "name": "B1",
                "channels": {
                    "1": "Channel 1",
                    "2": "Channel 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "2": {
                "name": "B1",
                "channels": {
                    "1": "Channel 1",
                    "2": "Channel 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "3": {
                "name": "Bank 2",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
            "4": {
                "name": "Bank 3",
                "channels": {
                    "1": "Ch. 1",
                    "2": "Ch. 2",
                    "3": "Ch. 3",
                    "4": "Ch. 4",
                    "5": "Ch. 5",
                    "6": "Ch. 6",
                    "7": "Ch. 7",
                    "8": "Ch. 8"
                }
            },
        }
    },
    ws_sender: mockClick,
    isChanged: false,
    updateFileName: mockUpdateFileName
};

describe('<PlanLoadPanel />', () => {
    const wrapper = shallow(<PlanLoadPanel {...defaultProps} />);
    const instance = wrapper.instance() as PlanLoadPanel;

    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('Renders Items', () => {
        instance.renderItem = jest.fn();
        instance.renderItem(0, 0);
        expect(instance.renderItem).toHaveBeenCalled();

        const test = mount(<PlanLoadPanel {...defaultProps}/>).find('ReactList');
        expect(test).toMatchSnapshot();
        expect(test.find('button').at(0).text()).toEqual('test.pln');
    });

    it('Cancel', () => {
        const cancel = wrapper.find('button#cancel');
        cancel.simulate('click');
        expect(mockClick).toBeCalled();
    });

    it('Load File', () => {
        // const test = mount(<PlanLoadPanel {...defaultProps}/>).find('ReactList');
        // expect(test).toMatchSnapshot();
        // expect(test.find('button').at(0).text()).toEqual('test.pln');
    });

    it('Delete File', () => {
        // const test = mount(<PlanLoadPanel {...defaultProps}/>).find('ReactList');
        // expect(test).toMatchSnapshot();
        // expect(test.find('button').at(0).text()).toEqual('test.pln');
    });
});