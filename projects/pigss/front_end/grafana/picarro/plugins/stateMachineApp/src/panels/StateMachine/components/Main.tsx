import React, { Component } from "react";
import PicarroAPI from "./../api/PicarroAPI";
import BankPanel from "./BankPanel";
import CommandPanel from "./CommandPanel";
import PlanPanel from "./PlanPanel";
import PlanLoadPanel from "./PlanLoadPanel";
import PlanSavePanel from "./PlanSavePanel";
import deepmerge from "deepmerge";
import Modal from "react-responsive-modal";
import { notifyError, notifySuccess } from '../utils/Notifications';
import { ModalInfo, PlanPanelTypes } from "./../types";
import EditPanel from "./EditPanel";
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
export class Main extends Component<any, any> {
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
    isChanged: false
  };
  constructor(props) {
    super(props);
    this.updateFileName = this.updateFileName.bind(this);
  }

  ws = new WebSocket(socketURL);
  componentDidMount() {
    this.getDataViaApi();

    this.ws.onopen = () => {
      notifySuccess("Web Socket Connected");
      // on connecting, do nothing but log it to the console
    };

    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      this.handleData(evt.data);
    };

    this.ws.onclose = () => {
      notifyError("web socket disconnected");
      this.ws = new WebSocket(socketURL);
      this.getDataViaApi();
    };
  }

  getDataViaApi = () => {
    let uiStatusData = PicarroAPI.getRequest(`http://${apiLoc}/uistatus`).then(
      response => {
        response.json().then(obj => {
          this.setState(deepmerge(this.state, { uistatus: obj }));
        });
      }
    );
    let planData = PicarroAPI.getRequest(`http://${apiLoc}/plan`).then(
      response => {
        response.json().then(obj => {
          this.setState(deepmerge(this.state, { plan: obj }));
        });
      }
    );
    let modalData = PicarroAPI.getRequest(`http://${apiLoc}/modal_info`).then(
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
          <PlanPanel
            uistatus={this.state.uistatus}
            plan={this.state.plan}
            setFocus={(row, column) => this.setFocus(row, column)}
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
      case PlanPanelTypes.SAVE:
        left_panel = (
          <PlanSavePanel
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

    let modalButtons = [];
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

    let bankPanels = [];
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
    return (
      <div style={{ textAlign: "center" }}>
        <div className="container-fluid">
          <div className="row justify-content-md-center">
            <div className="col-sm-3" style={{ height: "100%" }}>
              {left_panel}
            </div>
            <div
              className="col-sm-9"
              style={{ display: "grid", gridTemplateColumns: "1fr" }}
            >
              <div
                style={{
                  padding: "10px",
                  gridRowStart: "1",
                  gridColumnStart: "1"
                }}
              >
                {bankPanels}
              </div>
              {isPlan ? (
                <div className="ref-div">
                  <button
                    type="button"
                    onClick={e => this.ws_sender({ element: "reference" })}
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
