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

const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://localhost:1234/ws`;
const mockWS = jest.fn(element => {
  return element;
});
const server = new WS(socketURL);
const client = new WebSocket(socketURL);

describe("<PlanInformationPanelLayout />", () => {
  const wrapper = mount(<PlanInformationPanelLayout />);
  const instance = wrapper.instance() as PlanInformationPanelLayout;

  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });
 
});
