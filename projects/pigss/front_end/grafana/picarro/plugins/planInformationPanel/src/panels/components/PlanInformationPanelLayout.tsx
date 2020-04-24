import React, { Component } from "react";
import { PlanInformationPanel } from "./PlanInformationPanel";
import deepmerge from "deepmerge";
import { Plan } from "../types";
import API from "./../api/API";
import "./planInformation.css";

interface State {
  uistatus: { [key: string]: string };
  plan: Plan;
  initialized: boolean;
  timer: number;
  ws: WebSocket;
}

const REFRESH_INTERVAL = 5;
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
export class PlanInformationPanelLayout extends Component<any, any> {
  constructor(props) {
    super(props);
    this.state = {
      ws: null,
      timer: null,
      initialized: false,
      uistatus: {},
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
      },
    };
  }

  timeout = 250;
  ws = new WebSocket(socketURL);
  handleData(o: any) {
    if (this.state.initialized) {
      if ("uistatus" in o) {
        const uistatus = deepmerge(this.state.uistatus, o.uistatus);
        if (o.uistatus.timer) {
          this.setState({ timer: o.uistatus.timer });
        }

        this.setState({ uistatus });
      } else if ("plan" in o) {
        const plan = deepmerge(this.state.plan, o.plan);
        this.setState({ plan });
        const current_step = this.state.plan.current_step;
      }
    }
  }

  getDataViaApi = () => {
    const uiStatusData = API.getRequest(`http://${apiLoc}/uistatus`).then(
      (response) => {
        response.json().then((obj) => {
          this.setState(deepmerge(this.state, { uistatus: obj }));
        });
      }
    );
    const planData = API.getRequest(`http://${apiLoc}/plan`).then(
      (response) => {
        response.json().then((obj) => {
          this.setState(deepmerge(this.state, { plan: obj }));
        });
      }
    );
    Promise.all([uiStatusData, planData]).then(() => {
      this.setState(deepmerge(this.state, { initialized: true }));
    });
  };

  componentDidMount() {
    this.getDataViaApi();
    this.connect();
  }

  componentWillUnmount() {
    console.log("Component will unmount");
    if (this.ws && this.ws.readyState === 1) {
      this.ws.send("CLOSE");
      this.ws.close(1000, "Client Initited Connection Termination");
    }
  }

  connect = () => {
    const that = this;
    let connectInterval;

    this.ws.onopen = () => {
      this.setState({ ws: this.ws });
      that.timeout = 250;
      clearTimeout(connectInterval);
    };

    this.ws.onmessage = (evt) => {
      const message = JSON.parse(evt.data);
      this.handleData(message);
    };

    this.ws.onclose = (e) => {
      console.log(
        `Socket is closed. Reconnect will be attempted in ${Math.min(
          10000 / 1000,
          (that.timeout + that.timeout) / 1000
        )} second.`,
        e.reason
      );
      that.timeout = that.timeout + that.timeout; // increment retry interval
      connectInterval = setTimeout(this.check, Math.min(10000, that.timeout)); // call check function after timeout
    };
  };

  check = () => {
    const { ws } = this.state;
    if (!ws || ws.readyState == WebSocket.CLOSED) this.connect(); // check if websocket instance is closed, if so call `connect` function.
  };

  render() {
    return (
      <div id="outer">
        {this.state.initialized ? (
          <PlanInformationPanel
            uistatus={this.state.uistatus}
            plan={this.state.plan}
            timer={this.state.timer}
          />
        ) : null}
      </div>
    );
  }
}
