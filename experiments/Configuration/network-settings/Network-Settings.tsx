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
    inputEnabled: boolean;
    touched: object;
    valid: object;
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
      networkType: '',
      ip: '',
      gateway: '',
      netmask: '',
      dns: '',
      applyEnabled: false,
      undoEnabled: false,
      inputEnabled: true,
      touched: {
        ip: false,
        gateway: false,
        netmask: false,
        dns: false
      },
      valid: {
        ip: false,
        gateway: false,
        netmask: false,
        dns: false
      },
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
                    // Re-set all input fields as not touched since
                    // we are undoing all changes.
                    for (const key of Object.keys(newState['touched'])) {
                        newState['touched'][key] = false;
                    }
                }
                // Disable all input forms if DHCP is selected
                newState['inputEnabled'] = jsonData['networkType'] !== 'DHCP';
                this.setState(newState);
            });
        });
    }
    handleNetworkTypeChange = (event) => {
        const newState = { ...this.state };
        if (event.target.value === 'DHCP') {
            newState['ip'] = '';
            newState['gateway'] = '';
            newState['netmask'] = '';
            newState['dns'] = '';
            newState['inputEnabled'] = false;
        } else {
            newState['inputEnabled'] = true;
            this.getNetworkSettings(false);
        }
        newState['networkType'] = event.target.value;
        newState['applyEnabled'] = true;
        newState['undoEnabled'] = true;
        this.setState(newState);
    };
    handleInputChange = (event) => {
        const newState = { ...this.state };
        const { name, value } = event.target;
        let message = 'Error in: ';
        newState[name] = value;
        newState['undoEnabled'] = true;
        newState['touched'][name] = true;
        if (newState['networkType'] !== 'DHCP' ) {
            let count = 0;
            let validCount = 0;
            for (const key of Object.keys(newState['valid'])) {
                const validation = this.checkInput(newState[key]);
                count += 1;
                if (validation === true) {
                    validCount += 1;
                    newState['valid'][key] = true;
                } else {
                    message += key;
                    console.log(message);
                    newState['applyEnabled'] = false;
                    newState['valid'][key] = false;
                }
                if (count === validCount) {
                    newState['applyEnabled'] = true;
                }
            }
        } else {
            newState['applyEnabled'] = true;
        }
        this.setState(newState);
    };
    checkInput = (value) => {
        if (/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(value)) {
            return (true);
        } else {
          return (false);
        }
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
            newState['applyEnabled'] = false;
            newState['undoEnabled'] = false;
            this.setState(newState);
        });
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
                            onChange={this.handleNetworkTypeChange}
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
                    onChange={this.handleInputChange}
                    value={this.state.ip}
                    disabled={!this.state.inputEnabled}
                    name="ip"
                />
                <FormField
                    label="Gateway"
                    labelWidth={labelWidth}
                    onChange={this.handleInputChange}
                    value={this.state.gateway}
                    disabled={!this.state.inputEnabled}
                    name="gateway"
                />
                <FormField
                    label="Netmask"
                    labelWidth={labelWidth}
                    onChange={this.handleInputChange}
                    value={this.state.netmask}
                    disabled={!this.state.inputEnabled}
                    name="netmask"
                />
                <FormField
                    label="DNS"
                    labelWidth={labelWidth}
                    onChange={this.handleInputChange}
                    value={this.state.dns}
                    disabled={!this.state.inputEnabled}
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
