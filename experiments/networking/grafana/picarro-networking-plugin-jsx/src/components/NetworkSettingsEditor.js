import React, { Component } from 'react'
import { PanelOptionsGroup, FormField, Select } from '@grafana/ui'
import './App.css'

export class NetworkSettingsEditor extends Component {
  constructor(props) {
    super(props);
    this.modes = [
      {value: 'Static', label: 'Static'},
      {value: 'DHCP', label: 'DHCP'}
    ];
    this.state = {
      networkType: this.props.networkType,
      ip: this.props.ip,
      gateway: this.props.gateway,
      netmask: this.props.netmask,
      dns: this.props.dns,
      btnEnabled: false,
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleSelectChange = this.handleSelectChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }
  handleChange(event) {
    const { name, value } = event.target;
    this.setState({ [name]: value });
    this.setState({ btnEnabled: true });
  }
  /*
  handleSelectChange(event) {
    console.log(this.state);
    const { name, value } = event.target;
    console.log({[name]: value});
    this.setState({ [name]: value });
  }*/
  handleSelectChange(selection) {
    console.log(this.props);
    console.log(this.state);
    this.props.onChange( { ...this.state.networkType, selection: selection.value });
    console.log(this.state)
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
    })
    //this.setState({ btnEnabled: false })
  }
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


    const { options } = this.props;
    const { networkType } = options;
    return (
        <PanelOptionsGroup title="Network Settings">
          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
              <span className="gf-form-label width-10">
                Network Type
              </span>
              <Select
                options={this.modes}
                name="networkType"
                value={this.modes.find(e =>  e.value === 'Static' || 'DHCP' )}
                placeholder={this.state.networkType}
                onChange={this.handleSelectChange}
                isLoading={console.log('Loading!')}
                backspaceRemovesValue/>
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
            disabled={!this.state.btnEnabled}
            onClick={this.handleClick}
            >
            Apply
          </button>
          </div>
        </PanelOptionsGroup>
    )
  }
}

//value={this.modes.find(e => networkType === e.value)}
//export default NetworkSettingsEditor
