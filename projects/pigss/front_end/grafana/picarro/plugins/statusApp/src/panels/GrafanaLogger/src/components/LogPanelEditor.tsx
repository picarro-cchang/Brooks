import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps, Select, FormLabel } from '@grafana/ui';
import { LogProps } from './types';
import { LEVEL_OPTIONS, LIMIT_OPTIONS } from '../constants';

const labelWidth = 6;
const selectWidth = 12;

export class LogPanelEditor extends PureComponent<PanelEditorProps<LogProps>> {
  onLevelChange = (item: any) => {
    this.props.onOptionsChange({ ...this.props.options, level: [...item] });
  };
  onLimitChange = (limit: any) => {
    this.props.onOptionsChange({ ...this.props.options, limit: limit.value });
  };

  render() {
    const { level, limit } = this.props.options;

    return (
      <PanelOptionsGroup title="Configuration">
        <div className="row">
          <div className="gf-form col-md-3 col-sm-3">
            <FormLabel width={labelWidth}>Level</FormLabel>
            <Select
              options={LEVEL_OPTIONS}
              onChange={this.onLevelChange}
              value={level}
              backspaceRemovesValue
              isMulti={true}
            />
          </div>
          <div className="gf-form col-md-3 col-sm-3">
            <FormLabel width={labelWidth}>Limit</FormLabel>
            <Select
              width={selectWidth}
              options={LIMIT_OPTIONS}
              onChange={this.onLimitChange}
              value={LIMIT_OPTIONS.find(option => option.value === limit.toString())}
              backspaceRemovesValue
            />
          </div>
        </div>
      </PanelOptionsGroup>
    );
  }
}
