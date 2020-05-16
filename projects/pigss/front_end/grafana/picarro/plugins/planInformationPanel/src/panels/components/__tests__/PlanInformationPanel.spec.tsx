import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import { PlanInformationPanel, Props } from "./../PlanInformationPanel";
import "jest-fetch-mock";
import "react-toastify/dist/ReactToastify.css";
import mockData from "./../../api/__mocks__/mockData.json";
import mockPlan from "./../../api/__mocks__/mockPlan.json";

const defaultProps: Props = {
  uistatus: mockData,
  plan: mockPlan,
  timer: 30,
  runType: 2,
  currentPort: "Standby"
};

describe("<PlanInformationPanel />", () => {
  const getBankChannelFromStep = jest.spyOn(
    PlanInformationPanel.prototype,
    "getBankChannelFromStep"
  );
  const wrapper = mount(<PlanInformationPanel {...defaultProps} />);
  const instance = wrapper.instance() as PlanInformationPanel;

  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("getBankChannelFromStep", () => {
    const plan = wrapper.props().plan;
    plan.current_step = 12;
    wrapper.setProps({ plan });
    expect(getBankChannelFromStep).toHaveBeenCalled();
    plan.current_step = 3;
    wrapper.setProps({ plan });
    expect(getBankChannelFromStep).toHaveBeenCalled();
    plan.current_step = 2;
    wrapper.setProps({ plan });
    expect(getBankChannelFromStep).toHaveBeenCalled();
  });

  it("ACTIVE Plan", () => {
    const uistatus = wrapper.props().uistatus;
    uistatus.plan_loop = "ACTIVE";
    wrapper.setProps({ uistatus });
    expect(wrapper).toMatchSnapshot();
  });

  it("Last Step = 0", () => {
    const plan = wrapper.props().plan;
    plan.last_step = 0;
    wrapper.setProps({ plan });
    expect(wrapper).toMatchSnapshot();
    const div = wrapper.find("div").at(1);
    expect(div.text()).toEqual("No Plan Loaded");
  });
});
