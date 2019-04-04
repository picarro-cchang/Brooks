import React, { PureComponent } from 'react';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux';
import Page from 'app/core/components/Page/Page';
import { getNavModel } from 'app/core/selectors/navModel';
import { NavModel } from 'app/types';
import PicarroAPI from './api/PicarroAPI';
import { FormField } from '@grafana/ui';

export interface Props {
    navModel: NavModel;
}
export interface State {
    networkType: string;
    ip: string;
    gateway: string;
    netmask: string;
    dns: string;
    undoEnabled: boolean;
    applyEnabled: boolean;
}
const host = 'http://localhost:';
const port = '3030';
const getRoute = host + port + '/get_network_settings';
const postRoute = host + port + '/set_network_settings';
const labelWidth = 8;
const mapDispatchToProps = {};

export class NetworkSettings extends PureComponent<Props, State> {
    constructor(Props) {
    super(Props);
    this.state = {
      networkType: 'Static',
        ip: '',
        gateway: '',
        netmask: '',
        dns: '',
        applyEnabled: false,
        undoEnabled: false,
    };
    }
    componentDidMount() {
    this.getNetworkSettings(false);
    }
    getNetworkSettings (undo) {
        const newState = { ...this.state };
        PicarroAPI.getRequest(getRoute).then(response => {
            response.text().then(data => {
                const jsonData = JSON.parse(data);
                newState['networkType'] = jsonData['networkType'];
                newState['ip'] = jsonData['ip'];
                newState['gateway'] = jsonData['gateway'];
                newState['netmask'] = jsonData['netmask'];
                newState['dns'] = jsonData['dns'];
                if (undo === true) {
                    newState['applyEnabled'] = false;
                    newState['undoEnabled'] = false;
                }
                this.setState(newState);
            });
        });
    }
    onNetworkTypeChange = (event) => {
        const newState = { ...this.state };
        newState['networkType'] = event.target.value;
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        this.setState(newState);
    };
    onIPChange = (event) => {
        const newState = { ...this.state };
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        newState['ip'] = event.target.value;
        this.setState(newState);
    };
    onGatewayChange = (event) => {
        const newState = { ...this.state };
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        newState['gateway'] = event.target.value;
        this.setState(newState);
    };
    onNetmaskChange = (event) => {
        const newState = { ...this.state };
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        newState['netmask'] = event.target.value;
        this.setState(newState);
    };
    onDnsChange = (event) => {
        const newState = { ...this.state };
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        newState['dns'] = event.target.value;
        this.setState(newState);
    };
    handleApplyClick = () => {
        const newState = { ...this.state };
        console.log('click');
        PicarroAPI.postData(postRoute, {
            'networkType': this.state.networkType,
            'ip': this.state.ip,
            'gateway': this.state.gateway,
            'netmask': this.state.netmask,
            'dns': this.state.dns
        }).then(response => {
            response.text().then(text => console.log(text));
        });
        newState['applyEnabled'] = false;
        newState['undoEnabled'] = false;
        this.setState(newState);
    };
    handleUndoClick = () => {
        this.getNetworkSettings(true);
    };
  render() {
    const { navModel } = this.props;
    return (
      <Page navModel={navModel}>
        <Page.Contents>
                <div className="gf-form">
                    <span className="gf-form-label width-8">Network Type</span>
                    <div className="gf-form-select-wrapper max-width-12">
                        <select
                            className="input-small gf-form-input"
                            ng-change="ctrl.render()"
                            onChange={this.onNetworkTypeChange}
                            value={this.state.networkType}>
                            <option value="DHCP" key="DHCP">DHCP</option>
                            <option value="Static" key="Static">Static</option>
                        </select>
                    </div>
                </div>
            <div className="network-editor-form">
                <FormField
                    label="IP"
                    labelWidth={labelWidth}
                    onChange={this.onIPChange}
                    value={this.state.ip}
                    name="ip"
                />
                <FormField
                    label="Gateway"
                    labelWidth={labelWidth}
                    onChange={this.onGatewayChange}
                    value={this.state.gateway}
                    name="gateway"
                />
                <FormField
                    label="Netmask"
                    labelWidth={labelWidth}
                    onChange={this.onNetmaskChange}
                    value={this.state.netmask}
                    name="netmask"
                />
                <FormField
                    label="DNS"
                    labelWidth={labelWidth}
                    onChange={this.onDnsChange}
                    value={this.state.dns}
                    name="dns"
                />
            </div>
            <div className="gf-form-button-row">
                <button
                    className="apply-btn btn btn-primary"
                    disabled={!this.state.applyEnabled}
                    onClick={this.handleApplyClick}>
                    Apply
                </button>
                    <button
                        className="undo-btn btn btn-primary"
                        disabled={!this.state.undoEnabled}
                        onClick={this.handleUndoClick}>
                        Undo
                    </button>
            </div>
        </Page.Contents>
      </Page>
    );
    }
}

function mapStateToProps(state) {
    return {
    navModel: getNavModel(state.navIndex, 'network'),
    };
}

export default hot(module)(
    connect(
    mapStateToProps,
    mapDispatchToProps
    )(NetworkSettings)
);
