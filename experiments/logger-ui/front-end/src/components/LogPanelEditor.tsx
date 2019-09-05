import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps, Select, FormLabel, TimePicker } from '@grafana/ui';
import { TimeRange, dateTime } from '@grafana/data';
import { LogProps } from './types';

import { LEVEL_OPTIONS, LIMIT_OPTIONS, DEFAULT_TIME_OPTIONS } from '../constants';

const labelWidth = 6;
const selectWidth = 12;

export class LogPanelEditor extends PureComponent<PanelEditorProps<LogProps>> {
  onLevelChange = (item: any) => {
    this.props.onOptionsChange({ ...this.props.options, level: [...item] });
  }
  onLimitChange = (limit: any) => {
    this.props.onOptionsChange({ ...this.props.options, limit: limit.value });
  }
  onDateChange = (timeRange: TimeRange) => {
    this.props.onOptionsChange({ ...this.props.options, timeRange });
  };

  render() {
    const { level, limit, timeRange } = this.props.options;

    // Fix for grafana TimePicker issue, where from and to are string instead of DateTime Objects
    if (typeof timeRange.from === 'string') {
      timeRange.from = dateTime(timeRange.from);
    }
    if (typeof timeRange.to === 'string') {
      timeRange.to = dateTime(timeRange.to);
    }

    return (
      <PanelOptionsGroup title="Configuration">
        <div className="row">
          <div className="gf-form col-md-3 col-sm-3">
            <FormLabel width={labelWidth}>Level</FormLabel>
            <Select
              width={selectWidth}
              options={LEVEL_OPTIONS}
              onChange={this.onLevelChange}
              value={level}
              backspaceRemovesValue
              isLoading
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
              isLoading
            />
          </div>
          <div className="gf-form col-md-6 col-sm-6">
            <FormLabel width={labelWidth}>Date</FormLabel>

            <TimePicker
              timeZone="browser"
              selectOptions={DEFAULT_TIME_OPTIONS}
              onChange={this.onDateChange}
              value={timeRange}
              onMoveBackward={() => console.log('Move Backward')}
              onMoveForward={() => console.log('Move forward')}
              onZoom={() => console.log('Zoom')}
            />
          </div>
        </div>
      </PanelOptionsGroup>
    );
  }
}

