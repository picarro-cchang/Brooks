import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import "jest-fetch-mock";
import RunLayout from "../../components/Run/RunLayout";
import { RunLayoutProps, Plan } from "../../components/types";
import mockPlan from "../../api/__mocks__/mockPlan.json";
import mockData from "./../../api/__mocks__/mockData.json";
import LoadPanel from "../../components/Plan/LoadPanel";

const mockWS = jest.fn();
const mockLayoutSwitch = jest.fn();
const mockGetPlanFileNames = jest.fn();
jest.mock("./../../api/PlanService.ts")


const defaultProps: RunLayoutProps = {
  uistatus: mockData,
  plan: mockPlan,
  ws_sender: mockWS,
  fileNames: ["Test"],
  layoutSwitch: mockLayoutSwitch,
  loadedFileName: "Testing",
  getPlanFileNames: mockGetPlanFileNames
};
describe("<RunLayout />", () => {
  const deleteFile = jest.spyOn(RunLayout.prototype, "deleteFile");
  const updatePanelToShow = jest.spyOn(RunLayout.prototype, "updatePanelToShow");
  // const loadPlan = jest.spyOn(RunLayout.prototype, "loadPlan");
  const cancelLoadPlan = jest.spyOn(RunLayout.prototype, "cancelLoadPlan")

  const wrapper = shallow(<RunLayout {...defaultProps} />);
  const mountwrapper = mount(<RunLayout {...defaultProps} />)
  const instance = mountwrapper.instance() as RunLayout;

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Correct Component", () => {
    wrapper.setState({ panel_to_show: 1 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("PlanLoadPanel").html()).toBeDefined();
    wrapper.setState({ panel_to_show: 2 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("EditPanel").html()).toBeDefined();
    wrapper.setState({ panel_to_show: 3 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("PlanPreview").html()).toBeDefined();
  });

  it("updatePanelToShow", () => {
    mountwrapper.setState({panel_to_show: 0})
    const button = mountwrapper.find('CommandPanel').find('button#load-plan')
    // console.log("button", button.html())
    button.simulate('click');
    expect(updatePanelToShow).toHaveBeenCalled();
  });

  it("deleteFile", () => {
    wrapper.setState({ panel_to_show: 1 });
    const button = mountwrapper.find('PlanLoadPanel').find('button').at(1);
    button.simulate('click');
    expect(deleteFile).toHaveBeenCalled();
  });

  it("loadPlan", () => {
    wrapper.setState({ panel_to_show: 1 });
    const button = mountwrapper.find('PlanLoadPanel').find('button').at(0)
    button.simulate('click');
    // ex.toHaveBeenCalled();
  });

  it("cancelLoadPlan", () => {
    mountwrapper.setState({ panel_to_show: 3 });
    const button = mountwrapper.find('PlanPreview').find('button#cancel-load-plan')
    console.log("Button ", button.html())
    button.simulate('click');
    expect(cancelLoadPlan).toHaveBeenCalled();
  });
});
