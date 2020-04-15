import React, { ReactText } from "react";
import { shallow, mount, render } from "enzyme";
import WS from "jest-websocket-mock";
import "jest-styled-components";
import PlanLoadPanel from "./../../components/Plan/LoadPanel";
import { LoadPanelOptions } from "./../../components/types";
import mockLoadPanelData from "./../../api/__mocks__/mockLoadPanelData.json";

const mockClick = jest.fn(element => {
  return element;
});
const mockLoadPlan = jest.fn()
const mockUpdatePanel = jest.fn();
const mockUpdateFileName = jest.fn();
const mockDeleteFile = jest.fn();
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const defaultProps: LoadPanelOptions = {
  plan: mockLoadPanelData,
  updatePanel: mockUpdatePanel,
  fileNames: {
    1: "Test1",
    2: "Test2"
  },
  ws_sender: mockClick,
  isChanged: false,
  updateFileName: mockUpdateFileName,
  getPlanFromFileName: mockLoadPlan,
  deleteFile: mockDeleteFile
};

describe("<PlanLoadPanel />", () => {
  const wrapper = shallow(<PlanLoadPanel {...defaultProps} />);
  const instance = wrapper.instance() as PlanLoadPanel;
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Items", () => {
    instance.renderItem = jest.fn();
    instance.renderItem(0, 0);
    expect(instance.renderItem).toHaveBeenCalled();

    const fileList = mount(<PlanLoadPanel {...defaultProps} />).find(
      "ReactList"
    );
    expect(fileList).toMatchSnapshot();
    expect(
      fileList
        .find("button")
        .at(0)
        .text()
    ).toEqual("Test1");
  });

  it("Cancel", () => {
    const cancel = wrapper.find("button#cancel");
    cancel.simulate("click");
    expect(mockUpdatePanel).toBeCalled();
  });

  it("Load File", async () => {
    await server.connected;
    const fileButton = mount(<PlanLoadPanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(0);
    fileButton.simulate("click");
    const element = mockLoadPlan.mock.calls[0][0];
    client.send(element);
    expect(mockLoadPlan).toHaveBeenCalled();
    expect(mockLoadPlan).toHaveBeenCalled();
    await expect(server).toReceiveMessage("Test1");
    expect(server).toHaveReceivedMessages(["Test1"]);
    server.close;
  });

  it("Delete File", async () => {
    const deleteFile = mount(<PlanLoadPanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(1);
    expect(deleteFile.text()).toBe('X')   
  });
});
