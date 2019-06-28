import React, {Component, PureComponent} from 'react';
import PicarroAPI from '../api/PicarroAPI';
import BankPanel from './BankPanel';
import CommandPanel from './CommandPanel';

interface MainState {
    uistatus: object;
}

  
class Main extends Component<any, any> {
    state = { uistatus:{} };

    onButtonClick(e: any) {
        PicarroAPI.getRequest('http://localhost:8000/uistatus').then(
            response => {
                response.json().then(obj => {
                    this.setState({...{uistatus: obj}})
                })
            }
        );
    }

    render() {
        return (
            <div>
                <button
                    onClick={e => this.onButtonClick(e)}
                    className="btn btn-primary btn-lg">
                    Get Status
                </button>
                <div className="wrapper">
                    <CommandPanel uistatus={this.state.uistatus} />
                    <BankPanel bank={1} uistatus={this.state.uistatus} />
                    <BankPanel bank={2} uistatus={this.state.uistatus} />
                    <BankPanel bank={3} uistatus={this.state.uistatus} />
                    <BankPanel bank={4} uistatus={this.state.uistatus} />
                </div>
            </div>
        );
    }
}

export default Main;