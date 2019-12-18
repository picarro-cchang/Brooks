import React from 'react';
import BankPanel, {BankPanelOptions} from '../BankPanel';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";

const mockClick = jest.fn((element) => {return element;});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: BankPanelOptions = {
    bank: 1,
    uistatus: {
      bank: { "1": "READY" },
      clean: { "1": "READY" },
      channel: { "1": 
      { 
          "1": "AVAILABLE",
          "2": "DISABLED",
          "3": "READY",
          "4": "DISABLED",
          "5": "AVAILABLE",
          "6": "DISABLED",
          "7": "AVAILABLE",
          "8": "DISABLED"
        },
            },
        },
        ws_sender: mockClick,
        plan: {
          bank_names: {
            1: {
              name: "B 1",
              channels: { 
                  1: "Ch A",
                  2: "Channel 2",
                  3: "Ch 3",
                  4: "Ch 4",
                  5: "Ch 5",
                  6: "Ch 6",
                  7: "Ch 7",
                  8: "Ch 8"
                 },
            },
          },
        }
    };



describe('<BankPanel />', () => {
  const part = mount(<BankPanel {...defaultProps} />);
  const wrapper = shallow(<BankPanel {...defaultProps} />);

  it('Renders correctly', () => {
    expect(wrapper).toMatchSnapshot();
  });
  
  it('Contains Proper Channel Names', () => {
    const value1 = part.find('u.chn-name-1').text()
    const value2 = part.find('u.chn-name-2').text()
    expect(value1).toEqual('Ch A');
    expect(value2).toEqual('Channel 2');
  });

  it('Contains Proper Bank Name', () => {
    const value1 = part.find('h2').text()
    expect(value1).toEqual('B 1');
  });

  it('Contains correct status on channels', () => {
    const value = part.find('p#chn-status-1').text();
    expect(value).toEqual(' AVAILABLE ');
  });

  it('Check for  disabled/enabled property', () => {
    const value = part.find("button#channel-1").hasClass('disabled');
    const value2 = part.find("button#channel-2").hasClass('disabled');
    expect(value).toEqual(false);
    expect(value2).toEqual(true);
  });

  it("'WS onClick functionality'", async () => {
    const server = new WS(socketURL);
    const client = new WebSocket(socketURL);
    await server.connected;

    wrapper.find('button#channel-3').simulate('click');
    const element = mockClick.mock.calls[0][0];

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({element: "channel", bank: 1, channel: 3});
    expect(mockClick).toHaveReturnedWith({bank: 1, channel: 3, element: "channel"})
    expect(server).toHaveReceivedMessages([{element: "channel", bank: 1, channel: 3}]);
  });
});

