import React from "react";
import { mount } from "enzyme";
import Modal from "react-responsive-modal";
import "jest-styled-components";
import EditPanel from "./../../components/Run/EditPanel";
import EditForm from "./../../components/Run/EditForm";
import { EditPanelOptions } from "./../../components/types";
import WS from "jest-websocket-mock";
import mockPlan from "./../../api/__mocks__/mockPlan.json";
const mockClick = jest.fn(element => {
  return element;
});
const mockUpdatePanel = jest.fn(e => {return e})
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: EditPanelOptions = {
  planID: "",
  uistatus: {
    bank: {
      "1": "READY",
      "2": "DISABLED",
      "3": "READY",
      "4": "READY"
    }
  },
  plan: mockPlan,
  ws_sender: mockClick,
};

describe("<EditPanel />", () => {
  const wrapper = mount(<EditPanel {...defaultProps} />);
  const instance = wrapper.instance() as EditPanel;

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("handleSubmit calls validation and websocket if validation", () => {
    wrapper.find("form").simulate("submit", {
      preventDefault: () => {}
    });
    expect(mockClick).toHaveBeenCalled();
    mockClick.mockClear();
  });

  it("Test Modal is open", () => {
    wrapper.setState({ show: true });
    const modal = wrapper.find(Modal);
    expect(modal.props().open).toEqual(true);
    expect(wrapper).toMatchSnapshot();
  });

  it("Test handleClose", () => {
    wrapper
      .find(Modal)
      .props()
      .onClose();
    expect(wrapper.state("show")).toEqual(false);
  });

  it("Test Cancel", async () => {
    instance.setState({
      ...instance.state.prevState,
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
    const cancel = wrapper.find("button#cancel-btn");
    cancel.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "edit_cancel" });
    expect(server).toHaveReceivedMessages([{ element: "edit_cancel" }]);
    const test = wrapper.find(EditPanel).state().plan.bank_names;
    expect(test).toEqual(wrapper.state("prevState"));
    mockClick.mockClear();
  });

  it("handleBankChange", () => {
    wrapper
      .find(EditForm)
      .props()
      .handleBankChange("Bank 1", "1");
    expect(wrapper.find(EditPanel).state().plan.bank_names["1"].name).toEqual(
      "Bank 1"
    );
  });

  it("handleChannelNameChange", () => {
    wrapper
      .find(EditForm)
      .props()
      .handleChannelNameChange("Channel Number 2", "1", 2);
    expect(
      wrapper.find(EditPanel).state().plan.bank_names["1"].channels[2]
    ).toEqual("Channel Number 2");
  });

  it("Validate Form", () => {
    const component = new EditPanel(defaultProps);
    const boo = component.validateForm.call(defaultProps, [1, 3, 4]);
    expect(boo).toEqual(true);
  });
});

describe("<EditPanel /> Using Failing Channel Names", () => {
  const defaultPropsFail: EditPanelOptions = {
    planID: "",
    uistatus: {
      bank: {
        "1": "READY",
        "3": "READY",
        "4": "READY"
      }
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
      steps: {},
      num_plan_files: 0,
      plan_filename: "",
      plan_files: {},
      bank_names: {
        "1": {
          name: "Bank1",
          channels: {
            "1": "",
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
          name: "Bank2",
          channels: {
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
          name: "Bank 2",
          channels: {
            "1": "   ",
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
          name: "Bank 3",
          channels: {
            "1": "",
            "2": "Ch. 2",
            "3": "Ch. 3",
            "4": "Ch. 4",
            "5": "Ch. 5",
            "6": "Ch. 6",
            "7": "Ch. 7",
            "8": "Ch. 8"
          }
        }
      }
    },
    ws_sender: mockClick,
  };
  const component = new EditPanel(defaultPropsFail);

  it("Validate Form", () => {
    const valid = component.validateForm.call(defaultPropsFail, [3]);
    expect(valid).toEqual(false);
  });

  it("handleSubmit calls validation and websocket if validation", () => {
    expect(
      component.handleSubmit.call(defaultPropsFail, {
        preventDefault: () => {}
      })
    ).toBeUndefined();
  });
});
