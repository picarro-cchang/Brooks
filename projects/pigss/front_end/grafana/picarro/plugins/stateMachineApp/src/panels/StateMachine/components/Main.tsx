import React, { Component } from "react";
import PicarroAPI from "../api/PicarroAPI";
import deepmerge from "deepmerge";
import { notifyError } from "../utils/Notifications";
import { toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { PlanService } from "../api/PlanService";
import PlanLayout from "./Plan/PlanLayout";
import RunLayout from "./Run/RunLayout";
import { Plan } from "./types";

const REFRESH_INTERVAL = 5;
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;
export const storageKey = 'mainStorage';
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
    isPlanning: false,
    loadedFileName: "",
  };
  constructor(props) {
    super(props);
    this.getPlanFileNames = this.getPlanFileNames.bind(this);
    this.isPlanning = this.isPlanning.bind(this);
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

  async componentDidMount() {
    await this.getDataViaApi();
    this.attachWSMethods(this.ws);
    const storedPlanning = this.getStateFromSavedData();
    console.log("Stored Plan is ", storedPlanning)
    if(this.state.isPlanning != storedPlanning && storedPlanning != null){
      console.log("Doesn't match on Main. Main is: ", this.state.isPlanning)
      this.setState({
        isPlanning: storedPlanning,
      })
    }
  }

  componentWillUnmount() {
    console.log("Component will unmount, Saving Storage ", this.state.isPlanning);
    this.setPlanStorage(this.state.isPlanning)
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
    const planData = PicarroAPI.getRequest(
      `http://${apiLoc}/plan`
    ).then(response => {
      response.json().then(obj => {
        this.setState(deepmerge(this.state, { plan: obj }));
      });
    });
    const fileNames = PlanService.getFileNames().then(res => {
      res.json().then(obj => {
        console.log(obj)
        this.setState(deepmerge(this.state.fileNames, {fileNames: obj["plans"]}))
      })
    })
    Promise.all([uiStatusData, planData, fileNames]).then(() => {
      this.setState(deepmerge(this.state, { initialized: true }), () => {console.log("PLAN UPDATED ", this.state.plan)});
    });
  };


  handleData(data: any) {
    const o = JSON.parse(data);
    if (this.state.initialized) {
      if ("uistatus" in o) {
        const uistatus = deepmerge(this.state.uistatus, o.uistatus);
        this.setState({ uistatus });
      } else if ("plan" in o) {
        const plan = deepmerge(this.state.plan, o.plan);
        this.setState({ plan });
        // const fileNames = deepmerge(this.state.fileNames, o.plan.plan_files)
        // this.setState({fileNames})
      }
    }
  }

  ws_sender = (o: object) => {
    this.ws.send(JSON.stringify(o));
  };

  getPlanFileNames() {
    PlanService.getFileNames().then((repsonse: any) => 
    repsonse.json().then(planfiles => {
      if (planfiles['plans']) {
        this.setState({ fileNames: planfiles['plans'] });
      } else {
        console.log("There are no files")
      }
    })
    )
  }

  isPlanning() {
      this.setState({isPlanning: !this.state.isPlanning})
  }

  getPlanStorage = () => {
    // get picarroStorage object from sessionStorage
    if (window.sessionStorage) {
      return sessionStorage.getItem(storageKey);
    }
    return null;
  }

  setPlanStorage = (mainStorage: boolean) => {
    // set picarroStorage object in sessionStorage
    if (window.sessionStorage) {
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(mainStorage));
      } catch (error) {
        this.clearPlanStorage();
      }
    }
  }

  clearPlanStorage = () => {
    sessionStorage.removeItem(storageKey);
  }

  getStateFromSavedData = () => {
    const savedData = this.getPlanStorage();
    if (savedData !== null) {
      return (JSON.parse(savedData));
    }
    return null;
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
                    getPlanFileNames={this.getPlanFileNames}
                    loadedFileName={this.state.plan.plan_filename}
                />
            ):(
                <RunLayout
                    layoutSwitch={this.isPlanning}
                    fileNames={this.state.fileNames}
                    plan={this.state.plan}
                    uistatus={this.state.uistatus}
                    ws_sender={this.ws_sender}
                    loadedFileName={this.state.plan.plan_filename}
                    getPlanFileNames={this.getPlanFileNames}
                />
            )}

      
        </div>
    );
  }
}
        // <ToastContainer />
