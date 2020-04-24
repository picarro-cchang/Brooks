import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import { PlanInformationPanelLayout } from "./../PlanInformationPanelLayout";
import "jest-fetch-mock";
import "react-toastify/dist/ReactToastify.css";
import mockData from "./../../api/__mocks__/mockData.json";
import mockPlan from "./../../api/__mocks__/mockPlan.json";

jest.mock("./../../api/API.ts");

const socketURL = `ws://localhost:1234`;
const mockWS = jest.fn(element => {
  return element;
});
const server = new WS(socketURL, { jsonProtocol: true });
const client = new WebSocket(socketURL);

describe("<PlanInformationPanelLayout />", () => {
  const handleData = jest.spyOn(PlanInformationPanelLayout.prototype, "handleData");
  const componentWillUnmount = jest.spyOn(PlanInformationPanelLayout.prototype, "componentWillUnmount")
  const wrapper = mount(<PlanInformationPanelLayout />);
  const instance = wrapper.instance() as PlanInformationPanelLayout;

  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it('WebSocket Calls', async () => {
    instance.ws = client;
    instance.connect();
    await server.connected;
    server.send({"uistatus": {"timer": 5}})
    expect(handleData).toBeCalled();
    expect(instance.state.timer).toBe(5)
    server.send({"plan": {"current_step": 5}})
    expect(instance.state.plan.current_step).toBe(5)
    server.send({})
    expect(instance.state.plan.current_step).toBe(5)
    server.send({"uistatus": {"standby": "AVAILABLE"}})
    expect(handleData).toBeCalled();
  });

  it("Initialized State", async () => {
    instance.connect();
    await server.connected;
    instance.setState({initialized: false});
    server.send({});
    expect(handleData).toHaveBeenCalled();
  });
  

  it("componentWillUnmount", () => {
    wrapper.unmount()
    expect(componentWillUnmount).toHaveBeenCalled();
  });

  

 
});
