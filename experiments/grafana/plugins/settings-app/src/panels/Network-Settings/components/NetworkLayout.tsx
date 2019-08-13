import React, { Component } from 'react';
import {getRoute, NetworkProps} from '../types';
import PicarroAPI from "../api/PicarroAPI";

interface Props extends NetworkProps { }

export class NetworkLayout extends Component<Props, any> {
    constructor(props) {
        super(props);
        this.state = {
            networkType: this.props.options.networkType,
            ip: this.props.options.ip,
            gateway: this.props.options.gateway,
            netmask: this.props.options.netmask,
            dns: this.props.options.dns
        };
    }
    componentDidMount(): void {
        this.getNetworkSettings();
    }
    getNetworkSettings () {
        const newState = { ...this.state };
        PicarroAPI.getRequest(getRoute).then(response => {
            response.text().then(data => {
                const jsonData = JSON.parse(data);
                newState['networkType'] = jsonData['networkType'];
                newState['ip'] = jsonData['ip'];
                newState['gateway'] = jsonData['gateway'];
                newState['netmask'] = jsonData['netmask'];
                newState['dns'] = jsonData['dns'];
                this.setState(newState);
            });
        });
    }
    render() {
        return (
            <form className="gf-form-group ng-pristine ng-invalid network-grid">
                <div className="gf-form">
                    <span className="gf-form-label width-10">Network Type</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14 ng-not-empty ng-valid ng-valid-required"
                        value={this.state.networkType}
                        readOnly
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">IP</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        value={this.state.ip}
                        readOnly
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Gateway</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.gateway}
                        readOnly
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Netmask</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.netmask}
                        readOnly
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">DNS</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.dns}
                        readOnly
                    />
                </div>
            </form>
        );
    }
}
