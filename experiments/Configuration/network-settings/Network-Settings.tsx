import React, { PureComponent } from 'react';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux';
import Page from 'app/core/components/Page/Page';
import { getNavModel } from 'app/core/selectors/navModel';
import { NavModel } from 'app/types';
//import { FormField } from '@grafana/ui';
import PicarroAPI from './api/PicarroAPI';
//import {getRoute} from "../../networking/grafana/picarro-networking-plugin-tsx/src/types";

export interface Props {
    navModel: NavModel;
}

export interface State {
    networkType: string;
    ip: string;
    gateway: string;
    netmask: string;
    dns: string;
}

const host = 'http://localhost:';
const port = '3030';
const getRoute = host + port + '/get_network_settings';


export class NetworkSettings extends PureComponent<Props, State> {
    labelWidth = 8;

    constructor(Props) {
    super(Props);

    this.state = {
      networkType: '',
        ip: '',
        gateway: '',
        netmask: '',
        dns: ''
    };
    }

    componentDidMount() {
    this.getNetworkSettings();
    }

    getNetworkSettings () {
        const newState = { ...this.state };
        PicarroAPI.getRequest(getRoute).then(response => {
            response.text().then(data => {
                const jsonData = JSON.parse(data);
                /*
                this.state.onChange({ ...this.state.options, networkType: jsonData['networkType']});
                this.state.onChange({ ...this.state.options, ip: jsonData['ip']});
                this.state.onChange({ ...this.state.options, gateway: jsonData['gateway']});
                this.state.onChange({ ...this.state.options, netmask: jsonData['netmask']});
                this.state.onChange({ ...this.state.options, dns: jsonData['dns']});
                */
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
    const { navModel } = this.props;
    return (
      <Page navModel={navModel}>
        <Page.Contents>
            <form className="gf-form-group ng-pristine ng-invalid network-grid">
                <div className="gf-form">
                    <span className="gf-form-label width-10">Network Type</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14 ng-not-empty ng-valid ng-valid-required"
                        value={this.state.networkType}
                    />
                </div>

                <div className="gf-form">
                    <span className="gf-form-label width-10">IP</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        value={this.state.ip}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Gateway</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.gateway}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">Netmask</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.netmask}
                    />
                </div>
                <div className="gf-form">
                    <span className="gf-form-label width-10">DNS</span>
                    <input
                        type="text"
                        className="gf-form-input max-width-14"
                        placeholder=""
                        value={this.state.dns}
                    />
                </div>
            </form>
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

const mapDispatchToProps = {};

export default hot(module)(
    connect(
    mapStateToProps,
    mapDispatchToProps
    )(NetworkSettings)
);
