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

  onMinValueChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, slaveId: target.value });

  onMaxValueChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, tcpPort: target.value });

  render() {
    const { options } = this.props;
    const { slaveId, tcpPort } = options;

    return (
      <PanelOptionsGroup title="Simple options">
        <FormField
          label="Min value"
          labelWidth={this.labelWidth}
          onChange={this.onMinValueChange}
          value={slaveId}
        />
        <FormField
          label="Max value"
          labelWidth={this.labelWidth}
          onChange={this.onMaxValueChange}
          value={tcpPort}
        />
      </PanelOptionsGroup>
    );
  }
}
