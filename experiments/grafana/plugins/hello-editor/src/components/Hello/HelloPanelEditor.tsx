import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';
import { Select, FormLabel } from '@grafana/ui';
import { HelloOptions } from '../../types';

const labelWidth = 4;
const statOptions = [
  { value: 'World', label: 'World' },
  { value: 'Gerald', label: 'Gerald' },
  { value: 'Joel', label: 'Joel' },
  { value: 'Jordan', label: 'Jordan' },
  { value: 'Kevin', label: 'Kevin' }
];

export class HelloPanelEditor extends PureComponent<PanelEditorProps<HelloOptions>> {
  onNameChange = worldString =>
    this.props.onChange({ ...this.props.options, worldString: worldString.value });

  render() {
    const { worldString } = this.props.options;
    console.log(this.props.options);


    return (
      <PanelOptionsGroup title="Gauge value">
        <div className="gf-form">
          <FormLabel width={labelWidth}>Name</FormLabel>
          <Select
            width={8}
            options={statOptions}
            onChange={this.onNameChange}
            value={statOptions.find(option => option.value === worldString)}
            defaultValue={'World'}
           backspaceRemovesValue isLoading/>
        </div>
      </PanelOptionsGroup>
    );
  }
}
