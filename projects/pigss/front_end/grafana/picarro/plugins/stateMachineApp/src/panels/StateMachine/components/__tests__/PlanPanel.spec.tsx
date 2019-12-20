import React from 'react';
import {shallow, mount} from 'enzyme';
import 'jest-styled-components'
import WS from 'jest-websocket-mock';
import Modal from 'react-responsive-modal';
import PlanPanel from '../PlanPanel';
import {PlanPanelOptions, Plan} from '../../types';

const mockSetFocus = jest.fn();
const mockWSSender = jest.fn();
const mockUpdateFilename = jest.fn();

const defaultProps: PlanPanelOptions = {
    uistatus: {},
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
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename
};

describe('<PlanPanel />', () => {
    const wrapper = shallow(<PlanPanel {...defaultProps} />);
    const instance = wrapper.instance() as PlanPanel;

    it('Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('makePlanRow', ()=> {
        const value = instance.makePlanRow(5);
        expect(value).toMatchSnapshot();
    });

    it('manageFocus', ()=> {
    });

    it('renderItem', ()=> {
        instance.makePlanRow = jest.fn();
        const listItem = instance.renderItem(1,1);
        expect(instance.makePlanRow).toHaveBeenCalled();
        expect(listItem).toMatchSnapshot();
    });

    it('ReactList renders', ()=> {
        const planList = mount(<PlanPanel {...defaultProps} />);
        expect(planList).toMatchSnapshot();
        const channelInput = planList.find('input').at(0)
        channelInput.simulate('keyDown');
        // expect(channelInput.props().onFocus).toHaveBeenCalled();
        // expect(mockWSSender).toHaveBeenCalled();
    });

    it('Insert Button', () => {

    });

    it('Save Button', () => {

    });

    it('Load Button', () => {

    });

    it('Delete Button', () => {

    });

    it('Clear Button', () => {

    });

    it('Ok Button', () => {

    });
});