import React, {Component, PureComponent, useImperativeHandle} from 'react';
import PicarroAPI from '../api/PicarroAPI';
import BankPanel from './BankPanel';
import CommandPanel from './CommandPanel';
import Websocket from 'react-websocket';
import deepmerge from 'deepmerge';
 
interface MainState {
    initialized: boolean;
    uistatus: object;
}

  
class Main extends Component<any, any> {
    state = { initialized: false, uistatus: {} };
    refWebSocket: any;

    onButtonClick(e: any) {
        PicarroAPI.getRequest('http://localhost:8000/uistatus').then(
            response => {
                response.json().then(obj => {
                    // this.refWebSocket.sendMessage("message via websocket");
                    this.setState(deepmerge.all([this.state,{initialized: true, uistatus: obj}]));
                    console.log("State after uistatus", this.state);
                })
            }
        );
    }

    handleData(data:any) {
        console.log("Receiving from websocket", data);
        const o = JSON.parse(data);
        if (this.state.initialized) {
            const uistatus = deepmerge(this.state.uistatus, o);
            this.setState({uistatus: uistatus});    
            console.log("State after handleData", this.state);
        }
    }
  
    ws_sender = (o: object) => {
        console.log("Sending to websocket:", o);
        this.refWebSocket.sendMessage(JSON.stringify(o));
    };

    render() {
        return (
            <div>
                <button
                    onClick={e => this.onButtonClick(e)}
                    className="btn btn-primary btn-lg">
                    Get Status
                </button>
                <div className="wrapper">
                    <CommandPanel uistatus={this.state.uistatus} ws_sender={this.ws_sender}/>
                    <BankPanel bank={1} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                    <BankPanel bank={2} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                    <BankPanel bank={3} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                    <BankPanel bank={4} uistatus={this.state.uistatus} ws_sender={this.ws_sender} />
                    <Websocket url='ws://localhost:8000/ws'
                        onMessage={this.handleData.bind(this)}
                        reconnect={true} debug={true}
                        ref={(Websocket: any) => {
                              this.refWebSocket = Websocket;
                            }                        
                        }/>
                </div>
            </div>
        );
    }
}

export default Main;