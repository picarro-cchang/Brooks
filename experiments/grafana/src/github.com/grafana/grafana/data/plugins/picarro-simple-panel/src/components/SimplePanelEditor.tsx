// Libraries
import React, { PureComponent } from 'react';

// Components
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';

// Types
import { FormField } from '@grafana/ui';
import { SimpleOptions } from '../types';

export class SimplePanelEditor extends PureComponent<
  PanelEditorProps<SimpleOptions>
> {
  labelWidth = 8;

  onMinValueChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, minValue: target.value });

  onMaxValueChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, maxValue: target.value });

  onTextValueChange = ({ target }) =>
    this.props.onChange({ ...this.props.options, textValue: target.value });

  render() {
    const { options } = this.props;
    const { minValue, maxValue, textValue } = options;

    return (
      <PanelOptionsGroup title="Simple options">
        <FormField
          label="Min value"
          labelWidth={this.labelWidth}
          onChange={this.onMinValueChange}
          value={minValue}
        />
        <FormField
          label="Max value"
          labelWidth={this.labelWidth}
          onChange={this.onMaxValueChange}
          value={maxValue}
        />
        <FormField
          label="Text"
          labelWidth={this.labelWidth}
          onChange={this.onTextValueChange}
          value={textValue}
        />
      </PanelOptionsGroup>
    );
  }
}
