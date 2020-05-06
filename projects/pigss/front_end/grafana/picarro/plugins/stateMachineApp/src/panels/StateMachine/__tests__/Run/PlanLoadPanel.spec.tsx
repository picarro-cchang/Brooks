import React, { ReactText } from "react";
import { shallow, mount, render } from "enzyme";
import WS from "jest-websocket-mock";
import "jest-styled-components";
import PlanLoadPanel from "./../../components/Run/PlanLoadPanel";
import { LoadPanelCommandOptions } from "./../../components/types";
import mockLoadPanelData from "./../../api/__mocks__/mockLoadPanelData.json";

const mockClick = jest.fn(element => {
  return element;
});
const mockLoadPlan = jest.fn()
const mockDeleteFile = jest.fn();
const mockUpdatePanel = jest.fn();
const mockCancelLoadPlan = jest.fn();
const mockGetPlanFromFileName = jest.fn();
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const defaultProps: LoadPanelCommandOptions = {
  plan: mockLoadPanelData,
  deleteFile: mockDeleteFile,
  updatePanel: mockUpdatePanel,
  fileNames: ["Test1","Test2"],
  cancelLoadPlan: mockCancelLoadPlan,
  ws_sender: mockClick,
  getPlanFromFileName: mockGetPlanFromFileName,
  loadedFileName: "Testing"
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
    console.log(mockClick.mock.calls)
    const element = mockClick.mock.calls[1][0];
    client.send(element);
    expect(mockGetPlanFromFileName).toHaveBeenCalled();
    await expect(server).toReceiveMessage({"element":"load_filename"});
    expect(server).toHaveReceivedMessages([{"element":"load_filename"}]);
    server.close;
  });

  it("Delete File", async () => {
    await server.connected;
    const deleteFile = mount(<PlanLoadPanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(1);
    deleteFile.simulate("click");
    const element = mockDeleteFile.mock.calls[0][0];
    client.send(element);
    expect(mockDeleteFile).toHaveBeenCalled();
    await expect(server).toReceiveMessage("Test1");
    expect(server).toHaveReceivedMessages(["Test1"
    ]);
    server.close;
  });
});
