import React, {Component} from "react"
import {
  ReactPanelPlugin,
  PanelProps,
  ThemeContext
} from '@grafana/ui';
import './App.css'

class NetworkFrame extends Component {
  constructor(props) {
    super(props);
    this.state = {
      networkType: '',
      ip: '',
      gateway: '',
      netmask: '',
      dns: '',
      fetch: null
    };
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
    return (
      <ThemeContext.Consumer>
        {theme => {
          return (
            <div>
              <NetworkGrid
                networkType={this.state.networkType}
                ip={this.state.ip}
                gateway={this.state.gateway}
                netmask={this.state.netmask}
                dns={this.state.dns}/>
            </div>
          )
        }}
      </ThemeContext.Consumer>
    )
  }
}

/*
///////////////////////////////////////////////////////////
Keep this function here. We may want to use this if the
decision is to use the grafana panel editor to change
the values of the form
///////////////////////////////////////////////////////////
*/



function NetworkGrid (props) {
  return (
    <form className="gf-form-group ng-pristine ng-invalid network-grid">
      <div className="gf-form">
        <span className="gf-form-label width-10">Network Type</span>
        <input
          type="text"
          className="gf-form-input max-width-14 ng-not-empty ng-valid ng-valid-required"
          placeholder=""
          value={props.networkType}
        />
      </div>

      <div className="gf-form">
        <span className="gf-form-label width-10">IP</span>
        <input
          type="text"
          className="gf-form-input max-width-14"
          placeholder=""
          value={props.ip}
        />
      </div>
      <div className="gf-form">
        <span className="gf-form-label width-10">Gateway</span>
        <input
          type="text"
          className="gf-form-input max-width-14"
          placeholder=""
          value={props.gateway}
        />
      </div>
      <div className="gf-form">
        <span className="gf-form-label width-10">Netmask</span>
        <input
          type="text"
          className="gf-form-input max-width-14"
          placeholder=""
          value={props.netmask}
        />
      </div>
      <div className="gf-form">
        <span className="gf-form-label width-10">DNS</span>
        <input
          type="text"
          className="gf-form-input max-width-14"
          placeholder=""
          value={props.dns}
        />
      </div>

    </form>
  )
}



/*
///////////////////////////////////////////////////////////
Keep this class here. We may want to use this if the
decision is to allow editing directly in the plug-in
as a panel, and not use the grafana panel editor
///////////////////////////////////////////////////////////
*/

/*
class NetworkGrid extends Component {
  constructor (props) {
    super(props);
    this.state = {
      networkType: this.props.networkType,
      ip: this.props.ip,
      gateway: this.props.gateway,
      netmask: this.props.netmask,
      dns: this.props.dns
    }
    this.handleChange = this.handleChange.bind(this)
  }

  handleChange(event) {
    const { name, value } = event.target
    this.setState({ [name]: value })
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
    return (
      <form className="gf-form-group ng-pristine ng-invalid" name="network-grid">
        <div className="gf-form" ng-style="{height: ctrl.height}">
          <span className="gf-form-label width-10">Network Type</span>
          <input
            type="text"
            className="gf-form-input max-width-10 ng-not-empty ng-valid ng-valid-required"
            placeholder={this.props.networkType}
            name="networkType"
            value={this.state.networkType}
            onChange={this.handleChange}
          />
        </div>

        <div className="gf-form" ng-style="{height: ctrl.height}">
          <span className="gf-form-label width-10">IP</span>
          <input
            type="text"
            className="gf-form-input max-width-10"
            placeholder=""
            name="ip"
            value={this.state.ip}
            onChange={this.handleChange}
          />
        </div>
        <div className="gf-form" ng-style="{height: ctrl.height}">
          <span className="gf-form-label width-10">Gateway</span>
          <input
            type="text"
            className="gf-form-input max-width-10"
            placeholder=""
            name="gateway"
            value={this.state.gateway}
            onChange={this.handleChange}
          />
        </div>
        <div className="gf-form" ng-style="{height: ctrl.height}">
          <span className="gf-form-label width-10">Netmask</span>
          <input
            type="text"
            className="gf-form-input max-width-10"
            placeholder=""
            name="netmask"
            value={this.state.netmask}
            onChange={this.handleChange}
          />
        </div>
        <div className="gf-form" ng-style="{height: ctrl.height}">
          <span className="gf-form-label width-10">DNS</span>
          <input
            type="text"
            className="gf-form-input max-width-10"
            placeholder=""
            name="dns"
            value={this.state.dns}
            onChange={this.handleChange}
          />
        </div>
      </form>
    )
  }
}
*/

export default NetworkFrame
