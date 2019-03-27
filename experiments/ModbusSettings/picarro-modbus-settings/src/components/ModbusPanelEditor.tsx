// Libraries
import React, { PureComponent } from 'react';

// Components
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';

// Types
import { FormField } from '@grafana/ui';
import { ModbusOptions } from '../types';

export class ModbusPanelEditor extends PureComponent<
  PanelEditorProps<ModbusOptions>
> {
  labelWidth = 8;

  onSalveIdChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, slaveId: target.value });

  onTCPPortChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, tcpPort: target.value });

  validatePort = ({ target }) => {
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
      if (slaveId === i) {
        slaveIdSelection.push(
          <option value={i} selected>
            {slaveId}
          </option>
        );
      } else {
        slaveIdSelection.push(<option value={i}>{i}</option>);
      }
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
