import React from "react";
import { mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import { Main } from "../components/Main";
import PicarroAPI from "../api/PicarroAPI";
import "jest-fetch-mock";
import { PlanPanelTypes } from "./../components/types";
import "react-toastify/dist/ReactToastify.css";
import { notifyError, notifySuccess } from "../utils/Notifications";
import mockPlan from "./../api/__mocks__/mockPlan.json";
import mockPlan2 from "./../api/__mocks__/mockPlanPanel.json";
import data from "./../api/__mocks__/mockData.json";
import mockModal from "./../api/__mocks__/mockModalInfo.json";

jest.mock("./../api/PicarroAPI.ts");
jest.mock("./../api/PlanService.ts")

const defaultState = {
  initialized: false,
  modal_info: {
    show: false,
    html: "",
    num_buttons: 0,
    buttons: {}
  },
  uistatus: {},
  plan: mockPlan2,
  options: {
    panel_to_show: 0
  },
  isPlan: true,
  isChanged: false
};

const uistatus = {
  initialized: true,
  uistatus: data
};

const modal_info = {
  initialized: false,
  modal_info: mockModal
};

const plan = {
  initialized: true,
  plan: mockPlan
};

const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://localhost:1234/ws`;
const mockWS = jest.fn(element => {
  return element;
});
const server = new WS(socketURL);
const client = new WebSocket(socketURL);

describe("<Main />", () => {
  const handleDataSpy = jest.spyOn(Main.prototype, 'handleData')
  const wrapper = mount(<Main />);
  wrapper.setState({ ...defaultState });
  const instance = wrapper.instance() as Main;

  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Check correct left panel is showing", () => {
    expect(instance.state.isPlanning).toEqual(false);
    expect(wrapper.find("RunLayout")).toBeDefined();
  });

  it("ComponentDidMount", async () => {
    const spy = jest.spyOn(Main.prototype, "componentDidMount");
    const wrapper = mount(<Main />);
    await expect(spy).toHaveBeenCalled();
    spy.mockReset();
    spy.mockRestore();
  });

  it("API test", async () => {
    const response = await (
      await PicarroAPI.getRequest(`http://${apiLoc}/uistatus`)
    ).json();
    expect(response).toEqual(uistatus.uistatus);
  });

  it("handleData", () => {
    instance.handleData(JSON.stringify(uistatus));
    instance.handleData(JSON.stringify(plan));
    instance.handleData(JSON.stringify(modal_info));
    instance.handleData(JSON.stringify({}));
    instance.setState({ initialized: false });
    instance.handleData(JSON.stringify({}));
  });

  it("WS", () => {
    instance.ws_sender(uistatus);
    expect(instance.ws.send).toBeTruthy();
  });

  it("Test Toast", () => {
    notifyError(
      <div>
        <h6>
          <b>Web Socket Disconnected!</b>
        </h6>
      </div>
    );
    const toast = wrapper.find("ToastContainer");
    expect(toast).toMatchSnapshot();
    notifySuccess(
      <div>
        <h6>
          <b>Web Socket Connected!</b>
        </h6>
      </div>
    );
    const toastSuccess = wrapper.find("ToastContainer");
    expect(toastSuccess).toMatchSnapshot();
  });

  it("Test WS", async ()=>{
    const data = '{"uistatus": {"timer": 5 }}'
    instance.ws = client;
    instance.attachWSMethods(instance.ws);
    await server.connected;
    console.log(data)
    console.log(JSON.parse(data))
    server.send(data);
    expect(handleDataSpy).toHaveBeenCalled();
    server.close();
    instance.ws.close();
    // expect(client).toReceiveMessage();
  })

  // server.close;
  // client.close;
});
