import React, { Component } from 'react';

import { ModbusProps } from '../../types';
import PicarroAPI from '../../api/PicarroAPI';

interface Props extends ModbusProps {}

export class ModbusLayout extends Component<Props, any> {
  constructor(props) {
    super(props);
    this.state = {
      ipAddress: '127.0.0.1',
      user: {},
      UserOrgInfo: {},
    };
  }

  componentDidMount() {
    this.getIpAddress();
    this.getUserInfo();
  }

  getIpAddress() {
    let newstate = { ...this.state };
    PicarroAPI.getRequest('http://localhost:4000/network').then(response => {
      newstate['ipAddress'] = response['ip'];
      this.setState(newstate);
    });
  }

  getUserInfo() {
    let newstate = { ...this.state };
    PicarroAPI.getRequest('http://localhost:3000/api/user')
      .then(response => {
        newstate['user'] = response;
      })
      .then(() => {
        var url = 'http://localhost:3000/api/users/';
        url += newstate['user']['id'];
        url += '/orgs';
        var auth = 'Basic ' + new Buffer('admin:admin').toString('base64');
        var header = new Headers();
        header.append('Authorization', auth);
        PicarroAPI.getRequestWithHeader(url, header).then(response => {
          newstate['UserOrgInfo'] = response[0];
          this.setState(newstate);
        });
      });
  }

  onSaveClick(options) {
    const { slaveId, tcpPort } = options;
    PicarroAPI.postData('http://localhost:4000/modbus_settings', {
      slave: slaveId,
      port: tcpPort,
      user: this.state.user['email'],
    });
  }

  render() {
    const { options } = this.props;
    const { slaveId, tcpPort } = options;
    let SaveButton;
    if (
      Object.keys(this.state.UserOrgInfo).length !== 0 &&
      this.state.UserOrgInfo['role'] !== 'Viewer'
    ) {
      SaveButton = (
        <div className="gf-form-button-row">
          <button
            onClick={() => this.onSaveClick(options)}
            className="btn btn-primary"
          >
            Save and Restart Server
          </button>
        </div>
      );
    }

    return (
      <div className="gf-form-group ng-pristine ng-invalid">
        <div>&nbsp;</div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">Ip Address</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={this.state.ipAddress}
            readOnly
          />
        </div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">Salve Id</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={slaveId}
            readOnly
          />
        </div>
        <div className="gf-form">
          <span className="gf-form-label min-width-10">TCP Port</span>
          <input
            type="text"
            className="gf-form-input"
            placeholder=""
            value={tcpPort}
            readOnly
          />
        </div>
        {SaveButton}
      </div>
    );
  }
}
