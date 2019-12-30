import React from 'react';
import {shallow, mount} from 'enzyme';
import 'jest-styled-components'
import WS from 'jest-websocket-mock';
import Modal from 'react-responsive-modal';
import PlanPanel from '../PlanPanel';
import {PlanPanelOptions, Plan} from '../../types';
import { Server } from 'mock-socket';

const mockSetFocus = jest.fn();
const mockUpdateFilename = jest.fn();
const mockWSSender = jest.fn((element) => {return element});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: PlanPanelOptions = {
    uistatus: {},
    plan: {
        max_steps: 32,
        panel_to_show: 1,
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
    const server = new WS(socketURL);
    const client = new WebSocket(socketURL);
    instance.manageFocus = jest.fn();

    it('Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('makePlanRow', ()=> {
        const value = instance.makePlanRow(5);
        expect(value).toMatchSnapshot();
    });

    it('manageFocus', ()=> {
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-port-1');
        elem.simulate('click');
        expect(shallow.props().plan.focus).toEqual({"column": 2, "row": 1});
    });

    it('onFocus for Plan Channel', async ()=> {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-port-1');
        elem.simulate('focus');
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_panel", "focus" : {"column": 1, "row": 1}})
        expect(server).toHaveReceivedMessages([{element: "plan_panel", "focus" : {"column": 1, "row": 1}}])
        mockWSSender.mockClear();
        server.close;
    });

    it('onChange for Plan Channel', ()=> {
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-port-1');
        elem.simulate('change');
        expect(mockUpdateFilename).toHaveBeenCalled();
    });

    it('onFocus for Plan Duration', async ()=> {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-duration-1');
        elem.simulate('focus');
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_panel", "focus" : {"column": 2, "row": 1}})
        expect(server).toHaveReceivedMessages([{element: "plan_panel", "focus" : {"column": 2, "row": 1}}])
        mockWSSender.mockClear();
        server.close;
    });

    it('onChange for Plan Duration', async ()=> {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-duration-1');
        elem.simulate('change');
        expect(mockUpdateFilename).toHaveBeenCalled();
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_panel", row: 1, duration: "30"})
        expect(server).toHaveReceivedMessages([{element: "plan_panel", row: 1, duration: "30"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('onChange for Plan Radio', async ()=> {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const planList = shallow.find('ReactList');
        const elem = planList.find('input#plan-row-1');
        elem.simulate('change');
        expect(mockUpdateFilename).toHaveBeenCalled();
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_panel", current_step: 1})
        expect(server).toHaveReceivedMessages([{element: "plan_panel", current_step: 1}])
        mockWSSender.mockClear();
        server.close;
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
    });

    it('Cancel X', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const insertButton = shallow.find("span#cancel-x");
        insertButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_cancel"})
        expect(server).toHaveReceivedMessages([{element: "plan_cancel"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Insert Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const insertButton = shallow.find("button#insert-btn");
        insertButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_insert"})
        expect(server).toHaveReceivedMessages([{element: "plan_insert"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Save Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const saveButton = shallow.find("button#save-btn");
        saveButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_save"})
        expect(server).toHaveReceivedMessages([{element: "plan_save"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Load Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const loadButton = shallow.find("button#load-btn");
        loadButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_load"})
        expect(server).toHaveReceivedMessages([{element: "plan_load"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Delete Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const deleteButton = shallow.find("button#delete-btn");
        deleteButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        expect(mockUpdateFilename).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_delete"})
        expect(server).toHaveReceivedMessages([{element: "plan_delete"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Clear Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const clearButton = shallow.find("button#clear-btn");
        clearButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        expect(mockUpdateFilename).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_clear"})
        expect(server).toHaveReceivedMessages([{element: "plan_clear"}])
        mockWSSender.mockClear();
        server.close;
    });

    it('Ok Button', async () => {
        mockWSSender.mockClear();
        await server.connected;
        const shallow = mount(<PlanPanel {...defaultProps} />)
        const okButton = shallow.find("button#ok-btn");
        okButton.simulate("click");
        const element = mockWSSender.mock.calls[0][0];
        client.send(element);
        expect(mockWSSender).toHaveBeenCalled();
        expect(mockUpdateFilename).toHaveBeenCalled();
        await expect(server).toReceiveMessage({element: "plan_ok"})
        expect(server).toHaveReceivedMessages([{element: "plan_ok"}])
        mockWSSender.mockClear();
        server.close;
    });
});