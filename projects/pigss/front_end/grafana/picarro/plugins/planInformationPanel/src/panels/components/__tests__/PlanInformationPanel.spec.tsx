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
    timer: 30
};

describe("<PlanInformationPanel />", () => {
    const componentDidUpdate = jest.spyOn(PlanInformationPanel.prototype, "componentDidUpdate");
    const getBankChannelFromStep = jest.spyOn(PlanInformationPanel.prototype, "getBankChannelFromStep");
    const wrapper = mount(<PlanInformationPanel {...defaultProps}/>);
    const instance = wrapper.instance() as PlanInformationPanel;

    it("Snapshot", () => {
        expect(wrapper).toMatchSnapshot();
        console.log(wrapper.props().plan.current_step)
    });

    it("componentDidUpdate", () => {
        const plan = wrapper.props().plan
        plan.current_step = 7;
        wrapper.setProps({plan})
        expect(wrapper.props().plan.current_step).toEqual(7);
        expect(componentDidUpdate).toHaveBeenCalled();
    });

    it("getBankChannelFromStep", () => {
        const plan = wrapper.props().plan
        plan.current_step = 12;
        wrapper.setProps({plan});
        expect(getBankChannelFromStep).toHaveBeenCalled();
    });
 
});
