import React, { Component, PureComponent, useImperativeHandle } from 'react';
import PicarroAPI from '../api/PicarroAPI';
import BankPanel from './BankPanel';
import CommandPanel from './CommandPanel';
import PlanPanel from './PlanPanel';
import PlanLoadPanel from './PlanLoadPanel';
import PlanSavePanel from './PlanSavePanel';
import Websocket from 'react-websocket';
import deepmerge from 'deepmerge';
import Modal from 'react-responsive-modal';
import { ModalInfo, PlanPanelTypes } from './Types';

const socketURL = `ws://${window.location.hostname}:8000/ws`
class Main extends Component<any, any> {
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
            plan_filename: ""
        }
    };

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
        let p1 = PicarroAPI.getRequest(`http://${window.location.hostname}:8000/uistatus`).then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge(this.state, { uistatus: obj }));
                })
            }
        );
        let p2 = PicarroAPI.getRequest(`http://${window.location.hostname}:8000/plan`).then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge(this.state, { plan: obj }));
                })
            }
        );
        let p3 = PicarroAPI.getRequest(`http://${window.location.hostname}:8000/modal_info`).then(
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
    }

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
                )
                break;
            case PlanPanelTypes.LOAD:
                left_panel = (
                    <PlanLoadPanel plan={this.state.plan}
                        ws_sender={this.ws_sender} />
                )
                break;
            case PlanPanelTypes.SAVE:
                left_panel = (
                    <PlanSavePanel plan={this.state.plan}
                        ws_sender={this.ws_sender} />
                )
                break;
        }

        let modalButtons = [];
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
            const modal_info = this.state.modal_info as ModalInfo;
            modalButtons.push(
                <button className={modal_info.buttons[i].className}
                    style={{ margin: "10px" }}
                    onClick={() => this.ws_sender({ element: modal_info.buttons[i].response })}>
                    {modal_info.buttons[i].caption}
                </button>
            )
        }

        return (
            <div>
                <div className="container-fluid">
                    <div className="row justify-content-md-center">
                        <div className="col-sm-3">
                            {left_panel}
                        </div>
                        <div className="col-sm-2">
                            <BankPanel bank={1} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                        </div>
                        <div className="col-sm-2">
                            <BankPanel bank={2} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                        </div>
                        <div className="col-sm-2">
                            <BankPanel bank={3} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                        </div>
                        <div className="col-sm-2">
                            <BankPanel bank={4} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                        </div>
                    </div>
                </div>
                <Modal open={this.state.modal_info.show} onClose={() => this.ws_sender({ element: "modal_close" })} center>
                    <div style={{ margin: "20px" }}>
                        <div dangerouslySetInnerHTML={{ __html: this.state.modal_info.html }}>
                        </div>
                    </div>
                    {modalButtons}
                </Modal>
            </div>
        );
    }
}

export default Main;
