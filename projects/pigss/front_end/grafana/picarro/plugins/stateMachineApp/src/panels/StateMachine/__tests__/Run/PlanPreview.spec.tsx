import React, { ReactText } from "react";
import { shallow, mount, render } from "enzyme";
import WS from "jest-websocket-mock";
import "jest-styled-components";
import PlanPreview from "./../../components/Run/PlanPreview";
import { LoadPanelCommandOptions, PreviewPanelOptions } from "./../../components/types";
import mockLoadPanelData from "./../../api/__mocks__/mockLoadPanelData.json";

const mockClick = jest.fn(element => {
  return element;
});
const mockLoadPlan = jest.fn()
const mockDeleteFile = jest.fn();
const mockUpdatePanel = jest.fn();
const mockCancelLoadPlan = jest.fn();
const mockSetModalInfo = jest.fn();

const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
const defaultProps: PreviewPanelOptions = {
  plan: mockLoadPanelData,
  updatePanel: mockUpdatePanel,
  fileNames: ["Test1","Test2"],
  cancelLoadPlan: mockCancelLoadPlan,
  ws_sender: mockClick,
  loadedFileName: "Testing",
  setModalInfo: mockSetModalInfo
};

describe("<PlanPreview />", () => {
  const wrapper = shallow(<PlanPreview {...defaultProps} />);
  const instance = wrapper.instance() as PlanPreview;

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Items", () => {
    instance.renderItem = jest.fn();
    instance.renderItem(0, 0);
    expect(instance.renderItem).toHaveBeenCalled();

    const fileList = mount(<PlanPreview {...defaultProps} />).find(
      "ReactList"
    );
    expect(fileList).toMatchSnapshot();
    expect(
      fileList
        .find("div")
        .at(1)
        .text()
    ).toEqual("1. 1: Channel 1 Duration: 30");
  });

  it("Cancel", () => {

  });

  it("Ok", () => {

  });

});
