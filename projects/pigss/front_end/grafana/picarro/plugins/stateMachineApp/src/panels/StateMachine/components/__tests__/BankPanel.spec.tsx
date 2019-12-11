import React from 'react';
import BankPanel, {BankPanelOptions} from '../BankPanel';
import renderer from 'react-test-renderer';
import { render } from '@testing-library/react';
import { shallow, mount } from 'enzyme';

    const defaultProps: BankPanelOptions = {
        bank: 1,
        uistatus: {
          bank: { "1": "ACTIVE" },
          clean: { "1": "READY" },
          channel: { "1": 
          { 
              "1": "AVAILABLE",
              "2": "DISABLED",
              "3": "AVAILABLE",
              "4": "DISABLED",
              "5": "AVAILABLE",
              "6": "DISABLED",
              "7": "AVAILABLE",
              "8": "DISABLED"
            },
            },
        },
        ws_sender() { return "Hello";},
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

const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

describe('<BankPanel />', () => {
  it('Renders correctly', async () => {
    const tree = shallow(<BankPanel {...defaultProps} />)
    expect(tree).toMatchSnapshot();
  });
  
  it('Contains Proper Channel Names', () => {
    const tree = mount(<BankPanel {...defaultProps} />)
    const value1 = tree.find('u.chn-name-1').text()
    const value2 = tree.find('u.chn-name-2').text()
    expect(value1).toEqual('Ch A');
    expect(value2).toEqual('Channel 2');
  });

  it('Contains Proper Bank Name', () => {
    const tree = shallow(<BankPanel {...defaultProps} />)
    const value1 = tree.find('h2').text()
    expect(value1).toEqual('B 1');
  });

  it('Contains correct status on channels', () => {
    const tree = mount(<BankPanel {...defaultProps}/>);
    const value = tree.find('p.chn-status-1').text();
    expect(value).toEqual(' AVAILABLE ');
  });

  //Check for classname disabled for channels if props say so

  //check color of banks/channels for props

  //check onclick for channels

  //check onclick for buttons

  // it('Connect WS response');
