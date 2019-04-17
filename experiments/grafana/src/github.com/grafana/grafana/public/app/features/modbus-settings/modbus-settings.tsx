import React, { PureComponent } from 'react';
import { hot } from 'react-hot-loader';
import { connect } from 'react-redux';
import Page from 'app/core/components/Page/Page';
import { getNavModel } from 'app/core/selectors/navModel';
import { NavModel } from 'app/types';
import { FormField } from '@grafana/ui';
const config = require('./conf.json');
import { PicarroAPI } from './api/PicarroAPI';

export interface Props {
  navModel: NavModel;
}

export interface State {
  ipAddress: string;
  user: object;
  userOrgInfo: object;
  slaveId: number;
  tcpPort: number;
}

export class ModbusSettings extends PureComponent<Props, State> {
  labelWidth = 8;

  constructor(Props) {
    super(Props);

    this.state = {
      ipAddress: '127.0.0.1',
      user: {},
      userOrgInfo: {},
      slaveId: 1,
      tcpPort: 50500,
    };
  }

  componentDidMount() {
    this.getModbusSettings();
  }

  getModbusSettings() {
    const newState = { ...this.state };
    let url = config.picarro_server_url + config.picarro_modbus_setting_route;
    PicarroAPI.getRequest(url)
      .then(response => {
        newState['slaveId'] = response['slave'];
        newState['tcpPort'] = response['port'];
      })
      .then(() => {
        url = config.grafana_backend_url + config.grafana_user_route;
        PicarroAPI.getRequest(url)
          .then(response => {
            newState['user'] = response;
          })
          .then(() => {
            url = config.grafana_backend_url + config.grafana_users_route + '/';
            url += newState['user']['id'];
            url += config.grafana_org_out;
            const auth =
              'Basic ' +
              new Buffer(config.grafana_admin_username + ':' + config.grafana_admin_password).toString('base64');
            const header = new Headers();
            header.append('Authorization', auth);
            PicarroAPI.getRequestWithHeader(url, header).then(response => {
              newState['userOrgInfo'] = response[0];
              this.setState(newState);
            });
          });
      });
  }

  onSaveClick() {
    const url = config.picarro_server_url + config.picarro_modbus_setting_route;
    PicarroAPI.postData(url, {
      slave: this.state.slaveId,
      port: this.state.tcpPort,
      user: this.state.user['email'],
    });
  }

  onSlaveIdChange(event) {
    const newState = { ...this.state };
    newState['slaveId'] = event.target.value;
    this.setState(newState);
  }

  onTCPPortChange(event) {
    const newState = { ...this.state };
    newState['tcpPort'] = event.target.value;
    this.setState(newState);
  }

  render() {
    const { navModel } = this.props;
    const slaveIdSelection = [];
    for (let i = 1; i < 52; i++) {
      slaveIdSelection.push(<option key={i}>{i}</option>);
    }
    return (
      <Page navModel={navModel}>
        <Page.Contents>
          <div className="gf-form">
            <label className="gf-form-label width-8">Slave ID</label>
            <div className="gf-form-select-wrapper max-width-12">
              <select
                className="input-small gf-form-input"
                ng-change="ctrl.render()"
                onChange={this.onSlaveIdChange.bind(this)}
                value={this.state.slaveId}
              >
                {slaveIdSelection}
              </select>
            </div>
          </div>

          <FormField
            label="TCP Port"
            labelWidth={this.labelWidth}
            onChange={this.onTCPPortChange.bind(this)}
            value={this.state.tcpPort}
          />

          <div className="gf-form-button-row">
            <button onClick={this.onSaveClick.bind(this)} className="btn btn-primary">
              Save and Restart Server
            </button>
          </div>
        </Page.Contents>
      </Page>
    );
  }
}

function mapStateToProps(state) {
  return {
    navModel: getNavModel(state.navIndex, 'modbus'),
  };
}

const mapDispatchToProps = {};

export default hot(module)(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )(ModbusSettings)
);
