import React, { ReactText } from "react";
import { shallow, mount, render } from "enzyme";
import WS from "jest-websocket-mock";
import "jest-styled-components";
import PlanLoadPanel from "../components/PlanLoadPanel";
import { PlanLoadPanelOptions } from "../types";
import mockLoadPanelData from "./../api/__mocks__/mockLoadPanelData.json";

const mockClick = jest.fn(element => {
  return element;
});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const mockUpdateFileName = jest.fn();
const defaultProps: PlanLoadPanelOptions = {
  plan: mockLoadPanelData,
  ws_sender: mockClick,
  isChanged: false,
  updateFileName: mockUpdateFileName
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
    ).toEqual("test.pln");
  });

  it("Cancel", () => {
    const cancel = wrapper.find("button#cancel");
    cancel.simulate("click");
    expect(mockClick).toBeCalled();
  });

  it("Load File", async () => {
    mockClick.mockClear();
    await server.connected;
    const fileButton = mount(<PlanLoadPanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(0);
    fileButton.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockUpdateFileName).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_load_filename",
      name: "test.pln"
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_load_filename", name: "test.pln" }
    ]);
    mockClick.mockClear();
    server.close;
  });

  it("Delete File", async () => {
    await server.connected;
    const deleteFile = mount(<PlanLoadPanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(1);
    deleteFile.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_delete_filename",
      name: "test.pln"
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_delete_filename", name: "test.pln" }
    ]);
    mockClick.mockClear();
    server.close;
  });
});
