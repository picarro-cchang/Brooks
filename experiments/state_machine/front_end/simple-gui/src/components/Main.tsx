import React, {Component, PureComponent, useImperativeHandle} from 'react';
import PicarroAPI from '../api/PicarroAPI';
import BankPanel from './BankPanel';
import CommandPanel from './CommandPanel';
import PlanPanel from './PlanPanel';
import Websocket from 'react-websocket';
import deepmerge from 'deepmerge'; 
import Modal from 'react-responsive-modal';

interface ButtonInfo {
    caption: string;
    className: string;
    response: string;
}

interface ModalInfo {
    show: boolean,
    html: string,
    num_buttons: number,
    buttons: { [key: string]: ButtonInfo }
}
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
            show: false,
            focus: {row: 0, column: 0},
            last_step: 0,
            steps: {}
        }
    };

    refWebSocket: any;

    componentDidMount() {
        this.onButtonGetStatusClick(null);
    }

    onButtonGetStatusClick(e: any) {
    	let baseUrl = window.location.href.replace("3001","8000");
        let p1 = PicarroAPI.getRequest(baseUrl + 'uistatus').then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge(this.state, {uistatus: obj}));
                })
            }
        );
        let p2 = PicarroAPI.getRequest(baseUrl + 'plan').then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge(this.state, {plan: obj}));
                })
            }
        );

        let p3 = PicarroAPI.getRequest(baseUrl + 'modal_info').then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge(this.state, {modal_info: obj}));
                })
            }
        );
        Promise.all([p1, p2, p3]).then(() => {
            this.setState(deepmerge(this.state, {initialized: true}));
            console.log("State after getting uistatus, plan and modal info", this.state);
        })
    }

    onButtonTogglePlanClick(e: any) {
        this.setState(deepmerge(this.state, {plan: {show: !this.state.plan.show}}));
    }

    /*
    setDuration(row: number, duration: string) {
        if (row <= this.state.plan.length) {
            if (!isNaN(Number(duration))) {
                let plan = [...this.state.plan];
                const item = {...plan[row-1], duration: Number(duration)};
                plan[row-1] = item;
                console.log("Item is ", item, plan);
                this.setState({plan})
            }
        }
    }
    */

    setFocus(row: number, column: number) {
        this.setState(deepmerge(this.state, {plan: {focus: { row, column }}}));
    }

    handleData(data:any) {
        console.log("Receiving from websocket", data);
        const o = JSON.parse(data);
        if (this.state.initialized) {
            if ("uistatus" in o) {
                const uistatus = deepmerge(this.state.uistatus, o.uistatus);
                this.setState({uistatus});
            }
            else if ("plan" in o) {
                const plan = deepmerge(this.state.plan, o.plan);
                this.setState({plan});    
            }
            else if ("modal_info" in o) {
                const modal_info = deepmerge(this.state.modal_info, o.modal_info);
                this.setState({modal_info});    
            }
        }
    }
  
    ws_sender = (o: object) => {
        console.log("Sending to websocket:", o);
        if (this.refWebSocket !== null) {
            this.refWebSocket.sendMessage(JSON.stringify(o));
        }
    };

    render() {
    	let baseUrl = window.location.href.replace("3001","8000").replace("http://", "");
        const left_panel = this.state.plan.show ? (
            <PlanPanel uistatus={this.state.uistatus} plan={this.state.plan} 
            setFocus={(row, column) => this.setFocus(row, column)} 
            ws_sender={this.ws_sender} />
        ) : (
            <CommandPanel uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
        );

        let modalButtons=[];
        for (let i=1; i<=this.state.modal_info.num_buttons; i++) {
            const modal_info = this.state.modal_info as ModalInfo;
            modalButtons.push(
                <button className={modal_info.buttons[i].className} 
                    style={{ margin: "10px"}}
                    onClick={() => this.ws_sender({element:modal_info.buttons[i].response})}>
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
                        <Websocket url={"ws://" + baseUrl + "ws"}
                            onMessage={this.handleData.bind(this)}
                            reconnect={true} debug={true}
                            ref={(Websocket: any) => {
                                if (Websocket != null) {
                                    this.refWebSocket = Websocket;
                                }
                            }                        
                        }/>
                    </div>
                </div>
                    <Modal open={this.state.modal_info.show} onClose={() => this.ws_sender({element:"modal_close"})} center>
                        <div style={{margin: "20px"}}>
                            <div dangerouslySetInnerHTML={{__html: this.state.modal_info.html}}>
                            </div>
                        </div>
                        {modalButtons}
                    </Modal>
            </div>
        );
    }
}

export default Main;

/*
<div>
<button
    onClick={e => this.onButtonGetStatusClick(e)}
    className="btn btn-primary btn-lg"
    style={{margin: "10px"}}>
    Get Status
</button>
<button
    onClick={e => this.onButtonTogglePlanClick(e)}
    className="btn btn-primary btn-lg"
    style={{margin: "10px"}}>
    Toggle Plan
</button>
</div>
*/
