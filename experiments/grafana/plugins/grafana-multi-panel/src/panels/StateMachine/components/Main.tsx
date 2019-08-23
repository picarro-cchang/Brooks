import React, { Component, PureComponent, useImperativeHandle } from 'react';
import PicarroAPI from './../api/PicarroAPI';
import BankPanel from './BankPanel';
import CommandPanel from './CommandPanel';
import OptionsPanel from './OptionsPanel';
// import OverridePanel from './OverridePanel';
import PlanPanel from './PlanPanel';
import PlanLoadPanel from './PlanLoadPanel';
import PlanSavePanel from './PlanSavePanel';
import deepmerge from 'deepmerge';
import Modal from 'react-responsive-modal';
import {ModalInfo, PlanPanelTypes} from './../types';
import EditPanel from "./EditPanel";


const apiLoc = `${window.location.hostname}:8004/controller`;
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
      focus: { row: 0, column: 0 },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: {
        1: {
          name: "Bank 1",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8",
          }
        },
        2: {
          name: "Bank 2",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8",
          }
        },
        3: {
          name: "Bank 3",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8",
          }
        },
        4: {
          name: "Bank 4",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8",
          }
        }
      },
    },
    options: {
      panel_to_show: 0
    }
  };
  constructor(props) {
    super(props);
  //  this.switchPanel = this.switchPanel.bind(this)
  }

  ws = new WebSocket(socketURL);
  componentDidMount() {
    this.getDataViaApi();

    this.ws.onopen = () => {
      // on connecting, do nothing but log it to the console
      console.log('web socket connected');
    }

    this.ws.onmessage = evt => {
      // on receiving a message, add it to the list of messages
      this.handleData(evt.data);
    }

    this.ws.onclose = () => {
      alert('web socket disconnected');
      this.ws = new WebSocket(socketURL);
      this.getDataViaApi();
    }
  }

  getDataViaApi = () => {
    let p1 = PicarroAPI.getRequest(`http://${apiLoc}/uistatus`).then(
        response => {
          response.json().then(obj => {
            // this.refWebSocket.sendMessage("message via websocket");
            this.setState(deepmerge(this.state, { uistatus: obj }));
          })
        }
    );
    let p2 = PicarroAPI.getRequest(`http://${apiLoc}/plan`).then(
        response => {
          response.json().then(obj => {
            // this.refWebSocket.sendMessage("message via websocket");
            this.setState(deepmerge(this.state, { plan: obj }));
          })
        }
    );
    let p3 = PicarroAPI.getRequest(`http://${apiLoc}/modal_info`).then(
        response => {
          response.json().then(obj => {
            // this.refWebSocket.sendMessage("message via websocket");
            this.setState(deepmerge(this.state, { modal_info: obj }));
          })
        }
    );
    Promise.all([p1, p2, p3]).then(() => {
      this.setState(deepmerge(this.state, { initialized: true }));
      console.log("State after getting uistatus, plan and modal info", this.state);
    })
  };

  setFocus(row: number, column: number) {
    this.setState(deepmerge(this.state, { plan: { focus: { row, column } } }));
  }

  handleData(data: any) {
    console.log("Receiving from websocket", data);
    const o = JSON.parse(data);
    if (this.state.initialized) {
      if ("uistatus" in o) {
        const uistatus = deepmerge(this.state.uistatus, o.uistatus);
        this.setState({ uistatus });
      }
      else if ("plan" in o) {
        const plan = deepmerge(this.state.plan, o.plan);
        this.setState({ plan });
      }
      else if ("modal_info" in o) {
        const modal_info = deepmerge(this.state.modal_info, o.modal_info);
        this.setState({ modal_info });
      }
    }
  }

  ws_sender = (o: object) => {
    console.log("Sending to websocket:", o);
    this.ws.send(JSON.stringify(o));
  };


  // switchPanel(value){
  //   this.setState({plan:{panel_to_show: value}} );
  //   console.log(this.state.plan.panel_to_show)
  // }


  render() {
    let left_panel;
    switch (this.state.plan.panel_to_show) {
      case PlanPanelTypes.NONE:
        left_panel = (<CommandPanel uistatus={this.state.uistatus} ws_sender={this.ws_sender} />);
        break;
      case PlanPanelTypes.PLAN:
        left_panel = (
            <PlanPanel uistatus={this.state.uistatus} plan={this.state.plan}
                       setFocus={(row, column) => this.setFocus(row, column)}
                       ws_sender={this.ws_sender} />
        );
        break;
      case PlanPanelTypes.LOAD:
        left_panel = (
            <PlanLoadPanel plan={this.state.plan}
                           ws_sender={this.ws_sender} />
        );
        break;
      case PlanPanelTypes.SAVE:
        left_panel = (
            <PlanSavePanel plan={this.state.plan}
                           ws_sender={this.ws_sender} />
        );
        break;
      case PlanPanelTypes.EDIT:
        left_panel = (
            <EditPanel  plan={this.state.plan} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
        );
        break;
    }


    let modalButtons = [];
    for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
      const modal_info = this.state.modal_info as ModalInfo;
      modalButtons.push(
          <button className={modal_info.buttons[i].className}
                  style={{ margin: "10px"}}
                  onClick={() => this.ws_sender({ element: modal_info.buttons[i].response })}>
            {modal_info.buttons[i].caption}
          </button>
      )
    }

    let bankPanels = [];
    if ("bank" in this.state.uistatus as any) {
      for (let i=1; i<=4; i++) {
        if ((this.state.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanels.push(
              <div className="col-sm-2">
                <BankPanel plan={this.state.plan} bank={i} key={i} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
              </div>
          )
        }

      }

    }


    return (
        <div style={{ textAlign: 'center' }}>
          <div className="container-fluid">
            <div className="row justify-content-md-center">
              <div className="col-sm-3">
                {left_panel}
              </div>
              {bankPanels}
            </div>
            {/*<div className="row" >*/}
            {/*  /!*<OptionsPanel uistatus={this.state.uistatus} ws_sender={this.ws_sender} plan={this.state.plan}/>*!/*/}
            {/*</div>*/}
          </div>

          <Modal open={this.state.modal_info.show} onClose={() => this.ws_sender({ element: "modal_close" })} center>
            <div style={{ margin: "20px"}}>
              <div dangerouslySetInnerHTML={{ __html: this.state.modal_info.html }}>
              </div>
            </div>
            {modalButtons}
          </Modal>
        </div>
    );
  }
}

//export default Main;






















// import React, { PureComponent } from "react";
// import { PanelProps, getTheme } from "@grafana/ui";
// import { Options } from "../types";
//
// interface Props extends PanelProps<Options> {}
//
// interface State {
//   error: string;
//   imageUrl: string;
// }
//
// export class Main extends PureComponent<Props, State> {
//
//   constructor(props) {
//     super(props);
//
//     this.state = {
//       error: null,
//       imageUrl: null
//     };
//   }
//
//   updateImage = () => {
//     if (!this.props.options.imageUrl) {
//       return;
//     }
//
//     fetch(this.props.options.imageUrl, {
//       method: "head",
//       mode: "cors"
//     })
//       .then(response => {
//         if (response.status >= 400) {
//           throw Error(response.statusText);
//         }
//
//         const url = this.props.options.imageUrl;
//         this.setState({imageUrl: url, error: null });
//
//       })
//       .catch((error: Error) =>
//         this.setState({
//           imageUrl: null,
//           error: error.message
//         })
//       );
//   };
//
//
//   componentDidMount() {
//     this.updateImage();
//   }
//
//
//   render() {
//     if (!this.state.imageUrl) {
//       return null;
//     }
//
//     if (this.state.error) {
//       const theme = getTheme();
//       return (
//         <strong style={{ color: theme.colors.critical }}>
//           Could not load image: {this.state.error}
//         </strong>
//       );
//     }
//
//     return (
//       <img Hello-Editor={this.state.imageUrl} width={this.props.width} height="auto" />
//     );
//   }
// }
