import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';
import { Select, FormLabel } from '@grafana/ui';
import { HelloOptions } from '../../types';

const labelWidth = 4;
const statOptions = [
  { value: 'World', label: 'World' },
  { value: 'Emma', label: 'Emma' },
  { value: 'Joel', label: 'Joel' },
  { value: 'Jordan', label: 'Jordan' },
  { value: 'Kevin', label: 'Kevin' },
];

export class HelloPanelEditor extends PureComponent<PanelEditorProps<HelloOptions>> {
  onNameChange = (name: any) => this.props.onOptionsChange({ ...this.props.options, name: name.value });

  render() {
    const { name } = this.props.options;
    console.log(this.props.options);

    return (
      <PanelOptionsGroup title="Gauge value">
        <div className="gf-form">
          <FormLabel width={labelWidth}>Name</FormLabel>
          <Select
            width={8}
            options={statOptions}
            onChange={this.onNameChange}
            value={statOptions.find(option => option.value === name)}
            defaultValue={'World'}
            backspaceRemovesValue
            isLoading
          />
        </div>
      </PanelOptionsGroup>
    );
  }
}
