import React from 'react';
import CommandPanel from '../CommandPanel';
import {CommandPanelOptions} from '../../types';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import { element } from 'prop-types';

const mockClick = jest.fn((element) => {return element;});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: CommandPanelOptions = {
    uistatus: {
        "standby": "ACTIVE ",
        "identify": "DISABLED",
        "run": "READY",
        "plan": "READY",
        "plan_run": "READY",
        "plan_loop": "READY",
        "reference": "READY",
        "edit": "READY",
    },
    ws_sender: mockClick,
    plan: {
        "max_steps": 32,
        "panel_to_show": 0,
        "current_step": 8,
        "focus": {
            "row": 15,
            "column": 1
        },
        "last_step": 14,
        "steps": {
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
            },
            "2": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 2
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "3": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 4
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "4": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 8
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "5": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 16
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "6": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 32
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "7": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 64
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "8": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 128
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "9": {
            "banks": {
                "1": {
                "clean": 1,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "10": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 1,
            "duration": 30
            },
            "11": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 1
                }
            },
            "reference": 0,
            "duration": 30
            },
            "12": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 2
                }
            },
            "reference": 0,
            "duration": 30
            },
            "13": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 4
                }
            },
            "reference": 0,
            "duration": 30
            },
            "14": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 8
                }
            },
            "reference": 0,
            "duration": 30
            }
        },
        "num_plan_files": 7,
        "plan_files": {
            "1": "1234567890123456789012345678",
            "2": "30_seconds",
            "3": "__default__",
            "4": "abcdefghijklmnopqrstwxyzabc",
            "5": "abcdefghijklmnopqrstwxyzabcd",
            "6": "kp_test",
            "7": "kp_test_2"
        },
        "plan_filename": "__default__",
        "bank_names": {
            "1": {
            "name": "Bank 1",
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
            "4": {
            "name": "Bank 4",
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
            }
        },
    }
};

describe('<CommandPanel />', () => {
    const wrapper = shallow(<CommandPanel {...defaultProps} />);
    const short = mount(<CommandPanel {...defaultProps} />);
    const instance = wrapper.instance() as CommandPanel;
    const server = new WS(socketURL);
    const client = new WebSocket(socketURL);
    
    it('Renders Correctly', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('Buttons Enabled/Disabled Accordingly', () => {
        const value = wrapper.find("button#identify").props().disabled;
        expect(value).toEqual(true);
    });

    it('getDisabled functionality', () => {
        expect(instance.getDisabled("standby")).toEqual(false);
        expect(instance.getDisabled("status")).toEqual(true);
    });

    it('getClassNameOpt functionality', () => {
        expect(instance.getClassNameOpt("status")).toEqual("");
    });

    it('Standby', async () => {

        await server.connected;

        wrapper.find('button#standby').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("standby");
        expect(mockClick).toHaveReturnedWith({element: "standby"})
        expect(server).toHaveReceivedMessages(["standby"]);
        mockClick.mockClear();
    });
    it('Identify', async () => {

        await server.connected;

        wrapper.find('button#identify').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("identify");
        expect(mockClick).toHaveReturnedWith({element: "identify"})
        expect(server).toHaveReceivedMessages(["identify"]);
        mockClick.mockClear();
    });

    it('Edit Plan', async () => {

        await server.connected;

        wrapper.find('button#edit-plan').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("plan");
        expect(mockClick).toHaveReturnedWith({element: "plan"})
        expect(server).toHaveReceivedMessages(["plan"]);
        mockClick.mockClear();
    });

    it('Run Channel', async () => {

        await server.connected;

        wrapper.find('button#run-channel').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("run");
        expect(mockClick).toHaveReturnedWith({element: "run"})
        expect(server).toHaveReceivedMessages(["run"]);
        mockClick.mockClear();
    });


    it('Run Plan', async () => {

        await server.connected;

        wrapper.find('button#run-plan').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("plan_run");
        expect(mockClick).toHaveReturnedWith({element: "plan_run"})
        expect(server).toHaveReceivedMessages(["plan_run"]);
        mockClick.mockClear();
    });

    it('Loop Plan', async () => {

        await server.connected;

        wrapper.find('button#loop-plan').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("plan_loop");
        expect(mockClick).toHaveReturnedWith({element: "plan_loop"})
        expect(server).toHaveReceivedMessages(["plan_loop"]);
        mockClick.mockClear();
    });

    it('Reference', async () => {

        await server.connected;

        wrapper.find('button#reference').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("reference");
        expect(mockClick).toHaveReturnedWith({element: "reference"})
        expect(server).toHaveReceivedMessages(["reference"]);
        mockClick.mockClear();
    });

    it('Edit Labels', async () => {

        await server.connected;

        wrapper.find('button#edit-labels').simulate('click');
        const element = mockClick.mock.calls[0][0]['element'];
        
        client.send(element);
        expect(mockClick).toHaveBeenCalled();
        await expect(server).toReceiveMessage("edit");
        expect(mockClick).toHaveReturnedWith({element: "edit"})
        expect(server).toHaveReceivedMessages(["edit"]);
        mockClick.mockClear();
    });

});