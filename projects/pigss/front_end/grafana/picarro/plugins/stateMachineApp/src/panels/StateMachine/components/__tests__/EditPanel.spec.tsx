import React from 'react';
import {shallow, mount, ReactWrapper} from 'enzyme';
import Modal from 'react-responsive-modal';
import 'jest-styled-components'
import EditPanel from '../EditPanel';
import { EditPanelOptions } from '../../types';
import { transformersUIRegistry } from '@grafana/ui';

const mockClick = jest.fn((element) => {return element});
const defaultProps: EditPanelOptions = {
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
        num_plan_files: 0,
        plan_filename: "",
        plan_files: {},
        bank_names: {
            "1": {
                "name": "B 1",
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
            "3": {
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
    ws_sender: mockClick
};

describe('<EditPanel />', () => {
    const wrapper = shallow(<EditPanel {...defaultProps} />);
    const part = mount(<EditPanel {...defaultProps}/>);

    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('Mock validateForm', () => {
        const instance = wrapper.instance() as EditPanel;
        instance.validateForm = jest.fn();
       
        
    });

    it('Mock handleSubmit', () => {
        const validateMock = jest.fn();
        // const instance = wrapper.instance() as EditPanel;
        // // instance.handleSubmit = jest.fn();
        // wrapper.find('form').simulate('submit');
        // expect(validateMock).toBeCalled();

    });

    it('Test Modal is open', () => {
        wrapper.setState({show: true});
        const modal = wrapper.find(Modal);
        expect(modal.props().open).toEqual(true);
        expect(wrapper).toMatchSnapshot();
    });

    it('Test handleClose', () => {
        wrapper.find(Modal).props().onClose()
        expect(wrapper.state('show')).toEqual(false);
    });

    it('Test Ok/Cancel WS', () => {

    });
});