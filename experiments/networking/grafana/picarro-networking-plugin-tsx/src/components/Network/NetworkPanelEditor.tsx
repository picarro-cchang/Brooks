import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';
import { FormField, Select } from '@grafana/ui';
import { NetworkOptions } from '../../types';
//import PicarroAPI from '../../api/PicarroAPI';

const networkOptions = [
  { value: 'Static', label: 'Static' },
  { value: 'DHCP', label: 'DHCP' }
];
const labelWidth = 8;

export class NetworkPanelEditor extends PureComponent<PanelEditorProps<NetworkOptions>> {
  constructor(props) {
    super(props);
      this.state = {
          networkType: '',
          ip: '',
          gateway: '',
          netmask: '',
          dns: '',
      };
    NetworkPanelEditor.handleClick = NetworkPanelEditor.handleClick.bind(this);
  }
  onNetworkTypeChange = networkType =>
    this.props.onChange({ ...this.props.options, networkType: networkType.value });
  onIPChange = event =>
    this.props.onChange( { ...this.props.options, ip: event.target.value });
  onGatewayChange = event =>
    this.props.onChange({ ...this.props.options, gateway: event.target.value });
  onNetmaskChange = event =>
    this.props.onChange({ ...this.props.options, netmask: event.target.value });
  onDnsChange = event =>
    this.props.onChange({ ...this.props.options, dns: event.target.value });
  /*
  handleClick() {
    console.log(this.state.networkType);
    fetch("http://localhost:3030/set_network_settings",
   {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      "networkType": this.state.networkType,
      "ip": this.state.ip,
      "gateway": this.state.gateway,
      "netmask": this.state.netmask,
      "dns": this.state.dns
    })
  });
  */
  static handleClick () {
    console.log('Click');
  }
  /*
  componentDidMount() {
      PicarroAPI.getRequest("http://localhost:3030/get_network_settings").then( response => {
          response.text().then(data => {
              console.log('get_network_settings: \n' +
                  'networkType: ' + data['networkType'] + '\n' +
                  'ip: ' + data['ip'] + '\n'
          )
          })
      });
  }
  */
    componentDidMount () {
        fetch("http://localhost:3030/get_network_settings")
            .then(response => response.json())
            .then(data => {
                this.setState(function () {
                    return {
                        networkType: data['networkType'],
                        ip: data['ip'],
                        gateway: data['gateway'],
                        netmask: data['netmask'],
                        dns: data['dns']
                    }
                })
            })
    }



  render() {
    const {
      networkType,
      ip,
      gateway,
      netmask,
      dns,
      //btnEnabled
    } = this.props.options;
    console.log(this.props.options);

    return (
        <PanelOptionsGroup title="Network Settings">
          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
              <span className="gf-form-label width-8">Network Type</span>
                <Select
                    width={6}
                    options={networkOptions}
                    onChange={this.onNetworkTypeChange}
                    value={networkOptions.find(option => option.value === networkType)}
                    backspaceRemovesValue isLoading
                />
            </div>
          </div>
          <div className="network-editor-form">
            <FormField
                label="IP"
                labelWidth={labelWidth}
                onChange={this.onIPChange}
                value={ip || ''}
            />
            <FormField
                label="Gateway"
                labelWidth={labelWidth}
                onChange={this.onGatewayChange}
                value={gateway || ''}
                placeholder={this.state.gateway}
            />
            <FormField
                label="Netmask"
                labelWidth={labelWidth}
                onChange={this.onNetmaskChange}
                value={netmask || ''}
            />
            <FormField
                label="DNS"
                labelWidth={labelWidth}
                onChange={this.onDnsChange}
                value={dns || ''}
            />
          </div>
          <div className="network-editor-button">
            <button
                className="btn btn-primary"
                //disabled={!btnEnabled}
                onClick={NetworkPanelEditor.handleClick}
            >
              Apply
            </button>
          </div>
        </PanelOptionsGroup>
    );
  }
}
