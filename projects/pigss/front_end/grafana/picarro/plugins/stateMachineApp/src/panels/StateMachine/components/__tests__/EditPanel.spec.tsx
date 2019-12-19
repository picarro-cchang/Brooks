import React from 'react';
import {shallow, mount} from 'enzyme';
import Modal from 'react-responsive-modal';
import 'jest-styled-components'
import EditPanel from '../EditPanel';
import { EditPanelOptions } from '../../types';
import EditForm from '../EditForm';
import { bool } from 'prop-types';
import WS from 'jest-websocket-mock';
 
const mockClick = jest.fn((element) => {return element});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: EditPanelOptions = {
    uistatus: {
        "bank": {
            "1": "READY",
            "3": "READY",
            "4": "READY"
          },
    },
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
    ws_sender: mockClick
};


describe('<EditPanel />', () => {
    const wrapper = shallow(<EditPanel {...defaultProps} />);
    const instance = wrapper.instance() as EditPanel;

    it('Match Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('Mock validateForm', () => {
        const bankList = [1, 3, 4];
        instance.validateForm = jest.fn((bankList) => {
            let bankValue;
            for (let key in bankList) {
                let bankNum = bankList[key].toString()
                bankValue = defaultProps.plan.bank_names[bankNum].name;
            if (bankValue.length < 1) {
                return false;
            } else if (bankValue.replace(/\s/g, "").length < 1) {
                return false;
            } else {
                for (let i = 1; i < 9; i++) {
                    const chanValue = defaultProps.plan.bank_names[bankNum].channels[i];
                    if (chanValue.length < 1) {
                    return false;
                } else if (chanValue.replace(/\s/g, "").length < 1) {
                    return false;
                }
                }
            }
            }
            return true;
            });
        const result = instance.validateForm(bankList)
        expect(instance.validateForm).toBeCalled();
        expect(result).toEqual(true);
    });

    it('handleSubmit calls validation and websocket', () => {
        wrapper.find('form').simulate('submit', {
            preventDefault: () => {
            }});
        expect(mockClick).toHaveBeenCalled();
        expect(instance.validateForm).toHaveBeenCalled();
        mockClick.mockClear();
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

    it('Test Cancel', async () => {
        wrapper.setState({
            prevState: {
                1: {
                    name: "Bank 1",
                    channels: {
                        1: "Channel 1",
                        2: "Channel 2",
                        3: "Channel 3",
                        4: "Channel 4",
                        5: "Channel 5",
                        6: "Channel 6",
                        7: "Channel 7",
                        8: "Channel 8"
                    }
                },
                2: {
                    name: "Bank 2",
                    channels: {
                        1: "Channel 1",
                        2: "Channel 2",
                        3: "Channel 3",
                        4: "Channel 4",
                        5: "Channel 5",
                        6: "Channel 6",
                        7: "Channel 7",
                        8: "Channel 8"
                    }
                },
                3: {
                    name: "Bank 3",
                    channels: {
                        1: "Channel 1",
                        2: "Channel 2",
                        3: "Channel 3",
                        4: "Channel 4",
                        5: "Channel 5",
                        6: "Channel 6",
                        7: "Channel 7",
                        8: "Channel 8"
                    }
                },
                4: {
                    name: "Bank 4",
                    channels: {
                        1: "Channel 1",
                        2: "Channel 2",
                        3: "Channel 3",
                        4: "Channel 4",
                        5: "Channel 5",
                        6: "Channel 6",
                        7: "Channel 7",
                        8: "Channel 8"
                    }
                }
        }
        });
        const server = new WS(socketURL);
        const client = new WebSocket(socketURL);
        await server.connected;
        //cancel should call ws, set state to previous state
        const cancel = wrapper.find('button#cancel-btn');
        cancel.simulate('click')
        const element = mockClick.mock.calls[0][0];
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "edit_cancel"})
        expect(server).toHaveReceivedMessages([{element: "edit_cancel"}])
        const test = wrapper.state('plan')['bank_names']
        expect(test).toEqual(wrapper.state('prevState'))
    });

    
});