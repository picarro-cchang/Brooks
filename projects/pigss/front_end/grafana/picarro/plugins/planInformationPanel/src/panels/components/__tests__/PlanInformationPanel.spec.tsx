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
  runType: 4,
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
    expect(div.text()).toEqual("Plan Running: __default__ Measuring Port: 6: Ch. 6  Remaining Time: 30 secondsNext Port:  Clean Bank 1 ");
  });

  it("No Plan Loaded", () => {
    wrapper.setProps({
      runType: 0,
      plan: {
        max_steps: 32,
        panel_to_show: 0,
        current_step: 1,
        focus: { row: 0, column: 0 },
        last_step: 0,
        steps: {},
        num_plan_files: 0,
        plan_files: {},
        plan_filename: "",
        bank_names: {
          1: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: "",
            },
          },
          2: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: "",
            },
          },
          3: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: "",
            },
          },
          4: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: "",
            },
          },
        },
      }
    });
    expect(wrapper).toMatchSnapshot();
    const div = wrapper.find("div").at(1);
    expect(div.text()).toEqual("Plan Loaded: No Plan Loaded Measuring Port: Standby ");
  });

  it("Single Port", () => {
    wrapper.setProps({runType: 3, currentPort: "2: Port 2"})
    const div = wrapper.find("div").at(1);
    expect(div.text()).toEqual("Plan Running: Single PortMeasuring Port: 2: Port 2 ");
  })
});
