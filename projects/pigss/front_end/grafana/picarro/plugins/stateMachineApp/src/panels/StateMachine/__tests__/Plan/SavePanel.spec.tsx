import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import "jest-fetch-mock";
import Modal from "react-responsive-modal";
import SavePanel from "../../components/Plan/SavePanel";
import { PlanSavePanelOptions, Plan } from "../../components/types";
import mockPlanSavePanel from "../../api/__mocks__/mockSavePanelData.json";

const mockClick = jest.fn(element => {
  return element;
});

const mockUpdatePanel = jest.fn();
const mockPlanSaved = jest.fn()
const mockDeleteFile = jest.fn();
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const mockUpdateFileName = jest.fn();
const defaultProps: PlanSavePanelOptions = {
  plan: mockPlanSavePanel,
  ws_sender: mockClick,
  isChanged: false,
  updateFileName: mockUpdateFileName,
  planSaved: mockPlanSaved,
  updatePanel: mockUpdatePanel,
  fileNames: {
    1: "Test"
  },
  deleteFile: mockDeleteFile
};

describe("<PlanSavePanel />", () => {
  const wrapper = shallow(<SavePanel {...defaultProps} />);
  const instance = wrapper.instance() as SavePanel;
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Items", () => {
    instance.renderItem = jest.fn();
    instance.renderItem(0, 0);
    expect(instance.renderItem).toHaveBeenCalled();

    const fileList = mount(<SavePanel {...defaultProps} />).find(
      "ReactList"
    );
    expect(fileList).toMatchSnapshot();
    expect(
      fileList
        .find("button")
        .at(0)
        .text()
    ).toEqual("Test");
  });

  it("Delete", () => {
    // const spy = jest.spyOn(SavePanel.prototype, 'deleteFile')
    const shal = mount(<SavePanel {...defaultProps}/>)
    const deleteFileName = shal.find("ReactList").find("button").at(1);    
    deleteFileName.simulate("click");
    expect(mockDeleteFile).toHaveBeenCalled();
  });

  it("onChange file name input", () => {
    const event = { target: { name: "input", value: "plan1" } };
    const fileInput = wrapper.find("input");
    fileInput.simulate("change", event);
    expect(wrapper.state("fileName")).toBe("plan1")
  });

  it("Cancel", () => {
    const cancel = wrapper.find("button").at(0);
    cancel.simulate("click");
    expect(mockUpdatePanel).toHaveBeenCalled();
  });

  it("Ok", () => {
    const ok = wrapper.find("button").at(1);
    ok.simulate("click");
    // expect(mockUpdateFileName).toHaveBeenCalled();
    expect(mockPlanSaved).toHaveBeenCalled();
  });
});
