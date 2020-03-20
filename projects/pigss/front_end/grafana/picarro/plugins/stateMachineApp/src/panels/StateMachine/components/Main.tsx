import React, { Component } from "react";
import PicarroAPI from "./../api/PicarroAPI";
import BankPanel from "./BankPanel";
import BankPanelPlan from "./BankPanelPlan";
import CommandPanel from "./CommandPanel";
import PlanPanelLayout from "./PlanPanelLayout";
import PlanLoadPanel from "./PlanLoadPanel";
import PlanSavePanel from "./PlanSavePanel";
import deepmerge from "deepmerge";
import Modal from "react-responsive-modal";
import { notifyError, notifySuccess } from "../utils/Notifications";
import { ModalInfo, PlanPanelTypes } from "./../types";
import EditPanel from "./EditPanel";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const REFRESH_INTERVAL = 5;
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
export class Main extends React.Component<any, any> {
  state = {
    initialized: false,
    modal_info: {
      show: false,
      html: "",
      num_buttons: 0,
      buttons: {}
    },
    uistatus: {},
    plan: {
      max_steps: 10,
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
            8: ""
          }
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
            8: ""
          }
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
            8: ""
          }
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
            8: ""
          }
        }
      }
    },
    options: {
      panel_to_show: 0
    },
    isPlan: false,
    isChanged: false,
    bankAdd: {},
    isLoaded: false
  };
  constructor(props) {
    super(props);
    this.updateFileName = this.updateFileName.bind(this);
    this.addChanneltoPlan = this.addChanneltoPlan.bind(this);
  }

  ws = new WebSocket(socketURL);

  attachWSMethods = (ws: WebSocket) => {
    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      this.handleData(evt.data);
    };

    this.ws.onclose = event => {
      if (event.code !== 1000) {
        this.setupWSComm();
      }
    };
  };

  setupWSComm = () => {
    if (this.ws.CLOSED || this.ws.readyState === 0) {
      setTimeout(() => {
        toast.dismiss();
        notifyError("Web Socket Disconnected. Retrying to connect the server.");
        this.ws = new WebSocket(socketURL);
        this.attachWSMethods(this.ws);
        this.getDataViaApi();
      }, REFRESH_INTERVAL * 1000);
    }
  };

  componentDidMount() {
    this.getDataViaApi();
    this.attachWSMethods(this.ws);
  }

  componentWillUnmount() {
    console.log("Component will unmount");
    if (this.ws && this.ws.readyState === 1) {
      this.ws.send("CLOSE");
      this.ws.close(1000, "Client Initited Connection Termination");
    }
  }

  getDataViaApi = () => {
    const uiStatusData = PicarroAPI.getRequest(
      `http://${apiLoc}/uistatus`
    ).then(response => {
      response.json().then(obj => {
        this.setState(deepmerge(this.state, { uistatus: obj }));
      });
    });
    const planData = PicarroAPI.getRequest(`http://${apiLoc}/plan`).then(
      response => {
        response.json().then(obj => {
          this.setState(deepmerge(this.state, { plan: obj }));
        });
      }
    );
    const modalData = PicarroAPI.getRequest(`http://${apiLoc}/modal_info`).then(
      response => {
        response.json().then(obj => {
          this.setState(deepmerge(this.state, { modal_info: obj }));
        });
      }
    );
    Promise.all([uiStatusData, planData, modalData]).then(() => {
      this.setState(deepmerge(this.state, { initialized: true }));
    });
  };

  setFocus(row: number, column: number) {
    this.setState(deepmerge(this.state, { plan: { focus: { row, column } } }));
  }

  handleData(data: any) {
    const o = JSON.parse(data);
    if (this.state.initialized) {
      if ("uistatus" in o) {
        const uistatus = deepmerge(this.state.uistatus, o.uistatus);
        this.setState({ uistatus });
      } else if ("plan" in o) {
        const plan = deepmerge(this.state.plan, o.plan);
        this.setState({ plan });
      } else if ("modal_info" in o) {
        const modal_info = deepmerge(this.state.modal_info, o.modal_info);
        this.setState({ modal_info });
      }
    }
  }

  ws_sender = (o: object) => {
    this.ws.send(JSON.stringify(o));
  };

  updateFileName(x: boolean) {
    this.setState({ isChanged: x });
  }

  addChanneltoPlan(bankx: number, channelx: number) {
    this.setState({
      bankAdd: {
        bank: bankx,
        channel: channelx
      }
    });
  }

  render() {
    let left_panel;
    let isPlan = false;
    switch (this.state.plan.panel_to_show) {
      case PlanPanelTypes.NONE:
        left_panel = (
          <CommandPanel
            plan={this.state.plan}
            uistatus={this.state.uistatus}
            ws_sender={this.ws_sender}
          />
        );
        break;
      case PlanPanelTypes.PLAN:
        left_panel = (
          <PlanPanelLayout
            uistatus={this.state.uistatus}
            plan={this.state.plan}
            setFocus={(row, column) => this.setFocus(row, column)}
            bankAddition={this.state.bankAdd}
            updateFileName={this.updateFileName}
            isChanged={this.state.isChanged}
            ws_sender={this.ws_sender}
          />
        );
        isPlan = true;
        break;
      case PlanPanelTypes.LOAD:
        left_panel = (
          <PlanLoadPanel
            plan={this.state.plan}
            updateFileName={this.updateFileName}
            isChanged={this.state.isChanged}
            ws_sender={this.ws_sender}
          />
        );
        break;
      case PlanPanelTypes.EDIT:
        left_panel = (
          <EditPanel
            plan={this.state.plan}
            uistatus={this.state.uistatus}
            ws_sender={this.ws_sender}
          />
        );
        break;
    }

    const modalButtons = [];
    for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
      const modal_info = this.state.modal_info as ModalInfo;
      modalButtons.push(
        <button
          className={modal_info.buttons[i].className}
          style={{ margin: "10px" }}
          onClick={() =>
            this.ws_sender({ element: modal_info.buttons[i].response })
          }
        >
          {modal_info.buttons[i].caption}
        </button>
      );
    }

    const bankPanels = [];
    if (("bank" in this.state.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.state.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanels.push(
            <div>
              <BankPanel
                plan={this.state.plan}
                bank={i}
                key={i}
                uistatus={this.state.uistatus}
                ws_sender={this.ws_sender}
              />
            </div>
          );
        }
      }
    }

    const bankPanelsEdit = [];
    if (("bank" in this.state.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.state.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanelsEdit.push(
            <div>
              <BankPanelPlan
                plan={this.state.plan}
                bank={i}
                key={i}
                uistatus={this.state.uistatus}
                ws_sender={this.ws_sender}
                addChanneltoPlan={this.addChanneltoPlan}
              />
            </div>
          );
        }
      }
    }

    return (
      <div style={{ textAlign: "center" }}>
        <div className="plan-info">
          Running Plan: {this.state.plan.plan_filename}
        </div>
        <div className="container-fluid">
          <div className="row justify-content-md-center">
            <div className="col-sm-3" style={{ height: "100%" }}>
              {left_panel}
            </div>
            <div
              className="col-sm-9"
              style={{ display: "grid", gridTemplateColumns: "1fr" }}
            >
              {isPlan ? (
                <div
                  style={{
                    padding: "10px",
                    gridRowStart: "1",
                    gridColumnStart: "1"
                  }}
                >
                  {bankPanelsEdit}
                </div>
              ) : (
                <div
                  style={{
                    padding: "10px",
                    gridRowStart: "1",
                    gridColumnStart: "1"
                  }}
                >
                  {bankPanels}
                </div>
              )}
              {isPlan ? (
                <div className="ref-div">
                  <button
                    type="button"
                    id="reference"
                    onClick={e => {
                      // this.ws_sender({ element: "reference" })
                      this.addChanneltoPlan(0, 0);
                    }}
                    className={"btn btn-large ref-btn"}
                    style={{ color: "black" }}
                  >
                    Reference
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <Modal
          styles={{ overlay: { color: "black" } }}
          open={this.state.modal_info.show}
          onClose={() => this.ws_sender({ element: "modal_close" })}
          center
        >
          <div style={{ margin: "20px" }}>
            <div
              dangerouslySetInnerHTML={{ __html: this.state.modal_info.html }}
            ></div>
          </div>
          {modalButtons}
        </Modal>
        <ToastContainer />
      </div>
    );
  }
}
