import React from "react";
import { shallow } from "enzyme";
import "jest-styled-components";
import "jest-fetch-mock";
import PlanLayout from "../../components/Plan/PlanLayout";
import { PlanLayoutProps } from "../../components/types";
import mockPlan from "../../api/__mocks__/mockPlan.json";
import mockData from "./../../api/__mocks__/mockData.json";
import LoadPanel from "../../components/Plan/LoadPanel";

const mockWS = jest.fn();
const mockLayoutSwitch = jest.fn();

const defaultProps: PlanLayoutProps = {
  uistatus: {
    standby: "ACTIVE",
    identify: "READY",
    loop_plan: "READY",
    run: "READY",
    plan: "READY",
    plan_run: "READY",
    plan_loop: "READY",
    reference: "READY",
    run_plan: "READY",
    edit: "READY"
  },
  plan: mockPlan,
  ws_sender: mockWS,
  fileNames: {},
  layoutSwitch: mockLayoutSwitch
};
describe("<PlanLayout />", () => {
  const wrapper = shallow(<PlanLayout {...defaultProps} />);
  const instance = wrapper.instance() as PlanLayout;

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

  it("getPlanFromFileName", () => {});

  it("planSaved", () => {});

  it("addChannelToPlan", () => {});

  it("updatePanelToShow", () => {});

  it("deleteFile", () => {});

  it("setFocus", () => {});

  it("updateFileName", () => {});

  it("Banks Render", () => {});
});
