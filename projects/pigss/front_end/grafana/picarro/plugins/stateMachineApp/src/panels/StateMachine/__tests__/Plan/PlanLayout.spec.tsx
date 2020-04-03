import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import "jest-fetch-mock";
import PlanLayout from "../../components/Plan/PlanLayout";
import { PlanLayoutProps, Plan } from "../../components/types";
import mockPlan from "../../api/__mocks__/mockPlan.json";
import mockData from "./../../api/__mocks__/mockData.json";
import LoadPanel from "../../components/Plan/LoadPanel";

const mockWS = jest.fn();
const mockLayoutSwitch = jest.fn();

const defaultProps: PlanLayoutProps = {
  uistatus: mockData,
  plan: mockPlan,
  ws_sender: mockWS,
  fileNames: {
    1: "Test"
  },
  layoutSwitch: mockLayoutSwitch
};
describe("<PlanLayout />", () => {
  const addChanneToPlanRef = jest.spyOn(PlanLayout.prototype, "addChanneltoPlan");
  const updatePanelToShow = jest.spyOn(PlanLayout.prototype, "updatePanelToShow");
  const updateFileName = jest.spyOn(PlanLayout.prototype, "updateFileName");

  const wrapper = shallow(<PlanLayout {...defaultProps} />);
  const mountwrapper = mount(<PlanLayout {...defaultProps} />)
  const instance = mountwrapper.instance() as PlanLayout;

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Correct Component", () => {
    wrapper.setState({ panel_to_show: 1 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("LoadPanel").html()).toBeDefined();
    wrapper.setState({ panel_to_show: 2 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("SavePanel").html()).toBeDefined();
  });

  it("getPlanFromFileName", () => {
    const getPlan = jest.spyOn(instance, "getPlanFromFileName");
    mountwrapper.setState({panel_to_show: 1})
    const load = mountwrapper.find('LoadPanel').find('button#plan-filename-1')
    load.simulate("click");
    expect(getPlan).toHaveBeenCalled()
  });

  it("planSaved", () => {
    const planSaved = jest.spyOn(instance, "planSaved");
    mountwrapper.setState({panel_to_show: 2})
    const load = mountwrapper.find('SavePanel').find('button#save-btn')
    load.simulate("click");
    expect(planSaved).toHaveBeenCalled()
  });

  it("addChannelToPlan", () => {
    const reference = mountwrapper.find('button#reference');
    reference.simulate("click");
    expect(addChanneToPlanRef).toHaveBeenCalled();
  });

  it("updatePanelToShow", () => {
    const button = mountwrapper.find('PlanPanel').find('button').at(2);
    button.simulate('click');
    expect(updatePanelToShow).toHaveBeenCalled();
  });

  it("updateFileName", () => {
    mountwrapper.setState({panel_to_show: 0})
    const button = mountwrapper.find('PlanPanel').find('input#plan-port-1');
    button.simulate('change');
    expect(updateFileName).toHaveBeenCalled();
  });

});
