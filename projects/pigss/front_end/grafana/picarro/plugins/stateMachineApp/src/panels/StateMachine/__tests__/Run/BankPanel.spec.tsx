import React from "react";
import "jest";
import BankPanel, { BankPanelOptions } from "../../components/Run/BankPanel";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import mockPlan from "./../../api/__mocks__/mockPlan.json";

const mockClick = jest.fn(element => {
  return element;
});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: BankPanelOptions = {
  bank: 1,
  planID: "",
  uistatus: {
    bank: { "1": "READY" },
    clean: { "1": "READY" },
    channel: {
      "1": {
        "1": "AVAILABLE",
        "2": "DISABLED",
        "3": "READY",
        "4": "DISABLED",
        "5": "AVAILABLE",
        "6": "DISABLED",
        "7": "AVAILABLE",
        "8": "DISABLED"
      }
    }
  },
  ws_sender: mockClick,
  plan: mockPlan
};

describe("<BankPanel />", () => {
  const part = mount(<BankPanel {...defaultProps} />);
  const wrapper = shallow(<BankPanel {...defaultProps} />);
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);

  it("Renders correctly", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Contains Proper Channel Names", () => {
    const value1 = part.find("u.chn-name-1").text();
    const value2 = part.find("u.chn-name-2").text();
    expect(value1).toEqual("1: Ch. 1");
    expect(value2).toEqual("2: Ch. 2");
  });

  it("Check for  disabled/enabled property", () => {
    const value = part.find("button#channel-1").hasClass("disabled");
    const value2 = part.find("button#channel-2").hasClass("disabled");
    expect(value).toEqual(false);
    expect(value2).toEqual(true);
  });

  it("'WS onClick functionality'", async () => {
    await server.connected;

    wrapper.find("button#channel-3").simulate("click");
    const element = mockClick.mock.calls[0][0];

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "channel",
      bank: 1,
      channel: 3
    });
    expect(mockClick).toHaveReturnedWith({
      bank: 1,
      channel: 3,
      element: "channel"
    });
    expect(server).toHaveReceivedMessages([
      { element: "channel", bank: 1, channel: 3 }
    ]);
    server.close;
  });

  it("Clean Button", async () => {
    mockClick.mockClear();
    await server.connected;

    const cleanButton = wrapper.find("button#clean");
    cleanButton.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "clean", bank: 1 });
    expect(server).toHaveReceivedMessages([{ element: "clean", bank: 1 }]);
    mockClick.mockClear();
    server.close;
  });

  it("Test Clean Button inactive", () => {
    const testProps: BankPanelOptions = {
      bank: 1,
      planID: "",
      uistatus: {
        bank: { "1": "READY" },
        clean: { "1": "DISABLED" },
        channel: {
          "1": {
            "1": "AVAILABLE",
            "2": "DISABLED",
            "3": "READY",
            "4": "DISABLED",
            "5": "AVAILABLE",
            "6": "DISABLED",
            "7": "AVAILABLE",
            "8": "DISABLED"
          }
        }
      },
      ws_sender: mockClick,
      plan: {
        max_steps: 32,
        panel_to_show: 0,
        current_step: 1,
        focus: { row: 0, column: 0 },
        last_step: 0,
        steps: {},
        num_plan_files: 0,
        plan_files: {},
        plan_filename: "",
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
            }
          }
        }
      }
    };
    const sample = shallow(<BankPanel {...testProps} />);
    expect(sample).toMatchSnapshot();
  });

  it("Else", () => {
    const testProps: BankPanelOptions = {
      bank: 1,
      planID: "",
      uistatus: {},
      ws_sender: mockClick,
      plan: {
        max_steps: 32,
        panel_to_show: 0,
        current_step: 1,
        focus: { row: 0, column: 0 },
        last_step: 0,
        steps: {},
        num_plan_files: 0,
        plan_files: {},
        plan_filename: "",
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
            }
          }
        }
      }
    };

    const wrapper = shallow(<BankPanel {...testProps} />);
    expect(wrapper).toMatchSnapshot();
  });
});
