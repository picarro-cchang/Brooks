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
      slaveId: this.props.options.slaveId,
      tcpPort: this.props.options.tcpPort,
    };
  }

  componentDidMount() {
    this.updateState();
  }

  componentWillReceiveProps(nextProps) {
    let newstate = { ...this.state };
    newstate['slaveId'] = nextProps.options.slaveId;
    newstate['tcpPort'] = nextProps.options.tcpPort;
    this.setState(newstate);
  }

  updateState() {
    let newstate = { ...this.state };
    PicarroAPI.getRequest('http://localhost:4000/modbus_settings')
      .then(response => {
        newstate['slaveId'] = response['slave'];
        newstate['tcpPort'] = response['port'];
      })
      .then(() => {
        PicarroAPI.getRequest('http://localhost:4000/network').then(
          response => {
            newstate['ipAddress'] = response['ip'];
          }
        );
      })
      .then(() => {
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
      });
  }

  onSaveClick() {
    PicarroAPI.postData('http://localhost:4000/modbus_settings', {
      slave: this.state.slaveId,
      port: this.state.tcpPort,
      user: this.state.user['email'],
    });
  }

  render() {
    let SaveButton;
    if (
      Object.keys(this.state.UserOrgInfo).length !== 0 &&
      this.state.UserOrgInfo['role'] !== 'Viewer'
    ) {
      SaveButton = (
        <div className="gf-form-button-row">
          <button
            onClick={() => this.onSaveClick()}
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
        {SaveButton}
      </div>
    );
  }
}
