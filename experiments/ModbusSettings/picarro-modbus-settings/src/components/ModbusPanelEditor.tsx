// Libraries
import React, { PureComponent } from 'react';

// Components
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';

// Types
import { FormField } from '@grafana/ui';
import { ModbusOptions } from '../types';
import PicarroAPI from '../api/PicarroAPI';

var config = require('../conf.json');

export class ModbusPanelEditor extends PureComponent<
  PanelEditorProps<ModbusOptions>
> {
  labelWidth = 8;

  componentDidMount() {
    this.getModbusSettings();
  }

  getModbusSettings() {
    let url = config.picarro_server_url + config.picarro_modbus_setting_route;
    PicarroAPI.getRequest(url)
      .then(response => {
        this.props.onChange({
          ...this.props.options,
          slaveId: response['slave'],
        });

        this.props.onChange({
          ...this.props.options,
          tcpPort: response['port'],
        });
      })
      .then(() => {
        url = config.grafana_backend_url + config.grafana_user_route;
        PicarroAPI.getRequest(url)
          .then(response => {
            this.props.onChange({
              ...this.props.options,
              user: response,
            });
          })
          .then(() => {
            var url =
              config.grafana_backend_url + config.grafana_users_route + '/';
            url += this.props.options.user['id'];
            url += config.grafana_org_out;
            var auth =
              'Basic ' +
              new Buffer(
                config.grafana_admin_username +
                  ':' +
                  config.grafana_admin_password
              ).toString('base64');
            var header = new Headers();
            header.append('Authorization', auth);
            PicarroAPI.getRequestWithHeader(url, header).then(response => {
              this.props.onChange({
                ...this.props.options,
                userOrgInfo: response[0],
              });
            });
          });
      });
  }

  onSalveIdChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, slaveId: target.value });

  onTCPPortChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, tcpPort: target.value });

  validatePort = ({ target }) => {
    console.log(target.value);
    if (target.value < 1024 || target.value > 65564) {
      alert('Invalide port value, port value has to be between 1024 and 65564');
      return;
    }
    this.onTCPPortChange(target);
  };

  onSaveClick(options) {
    const { slaveId, tcpPort, user } = options;
    let url = config.picarro_server_url + config.picarro_modbus_setting_route;
    PicarroAPI.postData(url, {
      slave: slaveId,
      port: tcpPort,
      user: user['email'],
    });
  }

  render() {
    const { options } = this.props;
    const { slaveId, tcpPort } = options;

    let slaveIdSelection = [];
    for (let i = 1; i < 52; i++) {
      slaveIdSelection.push(<option key={i}>{i}</option>);
    }
    return (
      <PanelOptionsGroup title="Modbus Settings">
        <div className="gf-form">
          <label className="gf-form-label width-8">Slave ID</label>
          <div className="gf-form-select-wrapper max-width-12">
            <select
              className="input-small gf-form-input"
              ng-change="ctrl.render()"
              onChange={this.onSalveIdChange}
              value={slaveId}
            >
              {slaveIdSelection}
            </select>
          </div>
        </div>

        <FormField
          label="TCP Port"
          labelWidth={this.labelWidth}
          onChange={this.onTCPPortChange}
          value={tcpPort}
        />

        <div className="gf-form-button-row">
          <button
            onClick={() => this.onSaveClick(options)}
            className="btn btn-primary"
          >
            Save and Restart Server
          </button>
        </div>
      </PanelOptionsGroup>
    );
  }
}
