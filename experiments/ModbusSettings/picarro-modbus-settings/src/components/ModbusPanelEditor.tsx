// Libraries
import React, { PureComponent } from 'react';

// Components
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';

// Types
import { FormField } from '@grafana/ui';
import { ModbusOptions } from '../types';
import PicarroAPI from '../api/PicarroAPI';

export class ModbusPanelEditor extends PureComponent<
  PanelEditorProps<ModbusOptions>
> {
  labelWidth = 8;

  componentDidMount() {
    this.getModbusSettings();
  }

  getModbusSettings() {
    PicarroAPI.getRequest('http://localhost:4000/modbus_settings').then(
      response => {
        this.props.onChange({
          ...this.props.options,
          slaveId: response['slave'],
        });

        this.props.onChange({
          ...this.props.options,
          tcpPort: response['port'],
        });
      }
    );
  }

  onSalveIdChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, slaveId: target.value });

  onTCPPortChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, tcpPort: target.value });

  validatePort = ({ target }) => {
    console.log('Called');
    if (target.value < 1024 || target.value > 65564) {
      alert('Invalide port value, port value has to be between 1024 and 65564');
      return;
    }
    this.onTCPPortChange(target);
  };

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
          <label className="gf-form-label width-8">Salve ID</label>
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
      </PanelOptionsGroup>
    );
  }
}
