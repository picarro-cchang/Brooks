import React from "react";
import CommandPanel from "./../../components/Run/CommandPanel";
import { CommandPanelOptions } from "./../../components/types";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import mockPlan from "./../../api/__mocks__/mockPlan.json";

const mockClick = jest.fn(element => {
  return element;
});
const mockUpdatePanel = jest.fn(e => {return e});
const mockSwitchLayout = jest.fn();
const mockSetModalInfo = jest.fn();
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: CommandPanelOptions = {
  planID: "",
  uistatus: {
    standby: "ACTIVE ",
    identify: "DISABLED",
    run: "READY",
    plan: "READY",
    plan_run: "READY",
    plan_loop: "READY",
    reference: "READY",
    edit: "READY"
  },
  ws_sender: mockClick,
  plan: mockPlan,
  updatePanel: mockUpdatePanel,
  layoutSwitch: mockSwitchLayout,
  loadedFileName: "Testing"
};

describe("<CommandPanel />", () => {
  const wrapper = shallow(<CommandPanel {...defaultProps} />);
  const instance = wrapper.instance() as CommandPanel;
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);

  it("Renders Correctly", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Buttons Enabled/Disabled Accordingly", () => {
    const value = wrapper.find("button#identify").props().disabled;
    expect(value).toEqual(true);
  });

  it("getDisabled functionality", () => {
    expect(instance.getDisabled("standby")).toEqual(false);
    expect(instance.getDisabled("status")).toEqual(true);
  });

  it("getClassNameOpt functionality", () => {
    expect(instance.getClassNameOpt("status")).toEqual("");
  });

  it("Standby", async () => {
    await server.connected;

    wrapper.find("button#standby").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("standby");
    expect(mockClick).toHaveReturnedWith({ element: "standby" });
    expect(server).toHaveReceivedMessages(["standby"]);
    mockClick.mockClear();
  });

  it("Identify", async () => {
    await server.connected;

    wrapper.find("button#identify").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("identify");
    expect(mockClick).toHaveReturnedWith({ element: "identify" });
    expect(server).toHaveReceivedMessages(["identify"]);
    mockClick.mockClear();
  });

  it("Edit Plan", async () => {
    wrapper.find("button#edit-plan").simulate("click");
    expect(mockSwitchLayout).toHaveBeenCalled();
    mockSwitchLayout.mockClear();
  });

  it("Run Channel", async () => {
    await server.connected;

    wrapper.find("button#run-channel").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("run");
    expect(mockClick).toHaveReturnedWith({ element: "run" });
    expect(server).toHaveReceivedMessages(["run"]);
    mockClick.mockClear();
  });

  it("Run Plan", async () => {
    await server.connected;

    wrapper.find("button#run-plan").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("plan_run");
    expect(mockClick).toHaveReturnedWith({ element: "plan_run" });
    expect(server).toHaveReceivedMessages(["plan_run"]);
    mockClick.mockClear();
  });

  it("Loop Plan", async () => {
    await server.connected;

    wrapper.find("button#loop-plan").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("plan_loop");
    expect(mockClick).toHaveReturnedWith({ element: "plan_loop" });
    expect(server).toHaveReceivedMessages(["plan_loop"]);
    mockClick.mockClear();
  });

  it("Reference", async () => {
    await server.connected;

    wrapper.find("button#reference").simulate("click");
    const element = mockClick.mock.calls[0][0].element;

    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage("reference");
    expect(mockClick).toHaveReturnedWith({ element: "reference" });
    expect(server).toHaveReceivedMessages(["reference"]);
    mockClick.mockClear();
  });

  it("Edit Labels", async () => {
    wrapper.find("button#edit-labels").simulate("click");
    expect(mockUpdatePanel).toHaveBeenCalledWith(2);
    mockUpdatePanel.mockClear();
  });
});
