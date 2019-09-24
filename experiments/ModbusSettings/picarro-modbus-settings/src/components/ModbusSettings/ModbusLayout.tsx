import React, { Component } from 'react';

import { ModbusProps } from '../../types';
import PicarroAPI from '../../api/PicarroAPI';

interface Props extends ModbusProps {}

var config = require('../../conf.json');

export class ModbusLayout extends Component<Props, any> {
  constructor(props) {
    super(props);
    this.state = {
      ipAddress: '127.0.0.1',
      user: this.props.options.user,
      UserOrgInfo: this.props.options.userOrgInfo,
      slaveId: this.props.options.slaveId,
      tcpPort: this.props.options.tcpPort,
    };
  }

  componentDidMount() {
    let newstate = { ...this.state };
    let url = config.picarro_server_url + config.picarro_modbus_setting_route;
    PicarroAPI.getRequest(url)
      .then(response => {
        newstate['slaveId'] = response['slave'];
        newstate['tcpPort'] = response['port'];
      })
      .then(() => {
        url = config.picarro_server_url + config.picarro_network_route;
        PicarroAPI.getRequest(url).then(response => {
          newstate['ipAddress'] = response['ip'];
          this.setState(newstate);
        });
      });
  }

  componentWillReceiveProps(nextProps) {
    let newstate = { ...this.state };
    newstate['slaveId'] = nextProps.options.slaveId;
    newstate['tcpPort'] = nextProps.options.tcpPort;
    newstate['user'] = nextProps.options.user;
    newstate['UserOrgInfo'] = nextProps.options.userOrgInfo;
    this.setState(newstate);
  }

  render() {
    return (
      <div className="gf-form-group ng-pristine ng-invalid">
        <div>&nbsp;</div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">IP Address</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={this.state.ipAddress}
            readOnly
          />
        </div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">Slave Id</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={this.state.slaveId}
            readOnly
          />
        </div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">TCP Port</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={this.state.tcpPort}
            readOnly
          />
        </div>
      </div>
    );
  }
}
