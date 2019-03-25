import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';
import { Select, FormField } from '@grafana/ui';
import { NetworkOptions } from '../../types';

const networkOptions = [
  { value: 'Static', label: 'Static' },
  { value: 'DHCP', label: 'DHCP' }
];

export class NetworkPanelEditor extends PureComponent<PanelEditorProps<NetworkOptions>> {
  constructor(props) {
    super(props);
    this.state = {
      ip: '',
      gateway: '',
      netmask: '',
      dns: '',
      btnEnabled: false
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }
  onNetworkTypeChange = networkType =>
    this.props.onChange({ ...this.props.options, networkType: networkType.value });
  handleChange(event) {
    const { name, value } = event.target;
    this.setState( { [name]: value });
    this.setState( { btnEnabled: true });
  }
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


  render() {
    const {
      networkType,
      ip,
      gateway,
      netmask,
      dns,
      btnEnabled
    } = this.props.options;
    console.log(this.props.options);


    return (
      /*
      <PanelOptionsGroup title="Gauge value">
        <div className="gf-form">
          <FormLabel width={labelWidth}>Name</FormLabel>
          <Select
            width={8}
            options={statOptions}
            onChange={this.onNameChange}
            value={statOptions.find(option => option.value === worldString)}
            defaultValue={'World'}
           backspaceRemovesValue isLoading/>
        </div>
      </PanelOptionsGroup>
      */
        <PanelOptionsGroup title="Network Settings">
          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
              <span className="gf-form-label width-10">
                Network Type
              </span>
              <Select
                  options={networkOptions}
                  name="networkType"
                  value={networkOptions.find(option => option.value === networkType)}
                  onChange={this.onNetworkTypeChange}
                  backspaceRemovesValue isLoading/>
            </div>
          </div>
          <div className="network-editor-form">
            <FormField
                label="IP"
                labelWidth="10"
                placeholder={this.props.ip}
                onChange={this.handleChange}
                value={this.state.ip}
                name="ip"
            />
            <FormField
                label="Gateway"
                labelWidth="10"
                placeholder={this.props.gateway}
                onChange={this.handleChange}
                value={this.state.gateway}
                name="gateway"
            />
            <FormField
                label="Netmask"
                labelWidth="10"
                placeholder={this.props.netmask}
                onChange={this.handleChange}
                value={this.state.netmask}
                name="netmask"
            />
            <FormField
                label="DNS"
                labelWidth="10"
                placeholder={this.props.dns}
                onChange={this.handleChange}
                value={this.state.dns}
                name="dns"
            />
          </div>
          <div className="network-editor-button">
            <button
                className="btn btn-primary"
                disabled={!btnEnabled}
                onClick={this.handleClick}
            >
              Apply
            </button>
          </div>
        </PanelOptionsGroup>
    );
  }
}
