import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import Modal from "react-responsive-modal";
import PlanSavePanel from "../components/PlanSavePanel";
import { PlanSavePanelOptions, Plan } from "../types";
import mockPlanSavePanel from "./../api/__mocks__/mockSavePanelData.json";

const mockClick = jest.fn(element => {
  return element;
});
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const mockUpdateFileName = jest.fn();
const defaultProps: PlanSavePanelOptions = {
  plan: mockPlanSavePanel,
  ws_sender: mockClick,
  isChanged: false,
  updateFileName: mockUpdateFileName
};

describe("<PlanSavePanel />", () => {
  const wrapper = shallow(<PlanSavePanel {...defaultProps} />);
  const instance = wrapper.instance() as PlanSavePanel;
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Items", () => {
    instance.renderItem = jest.fn();
    instance.renderItem(0, 0);
    expect(instance.renderItem).toHaveBeenCalled();

    const fileList = mount(<PlanSavePanel {...defaultProps} />).find(
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

  it("Overwrite", async () => {
    mockClick.mockClear();
    await server.connected;
    const fileName = mount(<PlanSavePanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(0);
    fileName.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_save_filename",
      name: "test.pln"
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_save_filename", name: "test.pln" }
    ]);
    mockClick.mockClear();
    server.close;
  });

  it("Delete", async () => {
    mockClick.mockClear();
    await server.connected;
    const deleteFileName = mount(<PlanSavePanel {...defaultProps} />)
      .find("ReactList")
      .find("button")
      .at(1);
    deleteFileName.simulate("click");
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

  it("onChange file name input", async () => {
    const event = { target: { name: "input", value: "plan1" } };
    mockClick.mockClear();
    await server.connected;
    const fileInput = wrapper.find("input");
    fileInput.simulate("change", event);
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_save_filename",
      name: "plan1"
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_save_filename", name: "plan1" }
    ]);
    mockClick.mockClear();
    server.close;
  });

  it("Cancel", async () => {
    mockClick.mockClear();
    await server.connected;
    const cancel = wrapper.find("button").at(0);
    cancel.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_save_cancel" });
    expect(server).toHaveReceivedMessages([{ element: "plan_save_cancel" }]);
    mockClick.mockClear();
    server.close;
  });

  it("Ok", async () => {
    mockClick.mockClear();
    await server.connected;
    const ok = wrapper.find("button").at(1);
    ok.simulate("click");
    const element = mockClick.mock.calls[0][0];
    client.send(element);
    expect(mockClick).toHaveBeenCalled();
    expect(mockUpdateFileName).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_save_ok" });
    expect(server).toHaveReceivedMessages([{ element: "plan_save_ok" }]);
    mockClick.mockClear();
    server.close;
  });
});
