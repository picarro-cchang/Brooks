import React, { Component } from "react";
import PicarroAPI from "../api/PicarroAPI";
import deepmerge from "deepmerge";
import { notifyError } from "../utils/Notifications";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { PlanService } from "../api/PlanService";
import PlanLayout from "./Plan/PlanLayout";
import RunLayout from "./Run/RunLayout";

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
      max_steps: 32,
      panel_to_show: 0,
      current_step: 1,
      focus: { row: 1, column: 1 },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: {
        1: {
          name: "",
          channels: {
            1: "Port 1",
            2: "Port 2",
            3: "Port 3",
            4: "Port 4",
            5: "Port 5",
            6: "Port 6",
            7: "Port 7",
            8: "Port 8"
          }
        },
        2: {
          name: "",
          channels: {
            1: "Port 9",
            2: "Port 10",
            3: "Port 11",
            4: "Port 12",
            5: "Port 13",
            6: "Port 14",
            7: "Port 15",
            8: "Port 16"
          }
        },
        3: {
          name: "",
          channels: {
            1: "Port 17",
            2: "Port 18",
            3: "Port 19",
            4: "Port 20",
            5: "Port 21",
            6: "Port 22",
            7: "Port 23",
            8: "Port 24"
          }
        },
        4: {
          name: "",
          channels: {
            1: "Port 25",
            2: "Port 26",
            3: "Port 27",
            4: "Port 28",
            5: "Port 29",
            6: "Port 30",
            7: "Port 31",
            8: "Port 32"
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
    isLoaded: false,
    fileNames: [],
    isPlanning: false
  };
  constructor(props) {
    super(props);
    this.getPlanFileNames = this.getPlanFileNames.bind(this);
    this.isPlanning = this.isPlanning.bind(this);
    this.getLastRunningPlan = this.getLastRunningPlan.bind(this);
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
    this.getPlanFileNames();
    this.getLastRunningPlan();
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
    Promise.all([uiStatusData]).then(() => {
      this.setState(deepmerge(this.state, { initialized: true }));
    });
  };


  handleData(data: any) {
    const o = JSON.parse(data);
    console.log("WS ", o)
    if (this.state.initialized) {
      if ("uistatus" in o) {
        const uistatus = deepmerge(this.state.uistatus, o.uistatus);
        this.setState({ uistatus });
      }
      // } else if ("modal_info" in o) {
      //   const modal_info = deepmerge(this.state.modal_info, o.modal_info);
      //   this.setState({ modal_info });
      // }
    }
  }

  ws_sender = (o: object) => {
    this.ws.send(JSON.stringify(o));
  };

  getPlanFileNames() {
    PlanService.getFileNames().then((repsonse: any) => 
    repsonse.json().then(planfiles => {
      this.setState({ fileNames: planfiles['plans'] }, () => console.log(this.state.fileNames));
    })
    )
  }

  planFileNameUpTop() {
    if (this.state.uistatus["plan_loop"] == "ACTIVE" || this.state.uistatus["plan_run"] == "ACTIVE") {
      return true
    } else {
      return false
    }
  }

  isPlanning() {
      this.setState({isPlanning: !this.state.isPlanning})
  }

  getLastRunningPlan() {
    PlanService.getLastRunning().then((response: any) => 
      response.json().then(data => {
        if (data["message"]) {
          console.log("No Plan I suppsoe")
        }          
        else {
          this.setState({plan: data['details']});
        }

      }))
  }

  render() {
  
    return (
        <div> 
            {this.state.isPlanning ? (
                <PlanLayout
                    layoutSwitch={this.isPlanning}
                    fileNames={this.state.fileNames}
                    plan={this.state.plan}
                    uistatus={this.state.uistatus}
                    ws_sender={this.ws_sender}
                    getPlanFileNames={this.getPlanFileNames}
                />
            ):(
                <RunLayout
                    layoutSwitch={this.isPlanning}
                    fileNames={this.state.fileNames}
                    plan={this.state.plan}
                    uistatus={this.state.uistatus}
                    ws_sender={this.ws_sender}
                />
            )}

      
        </div>
    );
  }
}


  //     <Modal
        //   styles={{ overlay: { color: "black" } }}
        //   open={this.state.modal_info.show}
        //   onClose={() => this.ws_sender({ element: "modal_close" })}
        //   center
        // >
        //   <div style={{ margin: "20px" }}>
        //     <div
        //       dangerouslySetInnerHTML={{ __html: this.state.modal_info.html }}
        //     ></div>
        //   </div>
        //   {modalButtons}
        // </Modal>
        // <ToastContainer />
