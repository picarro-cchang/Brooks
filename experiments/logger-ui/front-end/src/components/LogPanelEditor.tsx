import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps, Select, FormLabel, TimePicker } from '@grafana/ui';
import { dateTime } from '@grafana/data';
import { LogProps } from './types';

const labelWidth = 6;
const selectWidth = 12;

const levelOptions = [{ value: '10', label: '10' }, { value: '20', label: '20' }, { value: '30', label: '30' }];
const limitOptions = [{ value: '10', label: '10' }, { value: '20', label: '20' }, { value: '50', label: '50' }];

export class LogPanelEditor extends PureComponent<PanelEditorProps<LogProps>> {
  onLevelChange = (level: any) => this.props.onOptionsChange({ ...this.props.options, level: level.value });
  onLimitChange = (limit: any) => this.props.onOptionsChange({ ...this.props.options, limit: limit.value });
  onDateChange = (timeRange: any) => this.props.onOptionsChange({ ...this.props.options, date: timeRange });

  render() {
    console.log(this.props);
    const { level, limit } = this.props.options;
    return (
      <PanelOptionsGroup title="Configuration">
        <div className="row">
          <div className="gf-form col-md-3 col-sm-3">
            <FormLabel width={labelWidth}>Level</FormLabel>
            <Select
              width={selectWidth}
              options={levelOptions}
              onChange={this.onLevelChange}
              value={levelOptions.find(option => option.value === level)}
              defaultValue={'10'}
              backspaceRemovesValue
              isLoading
            />
          </div>
          <div className="gf-form col-md-3 col-sm-3">
            <FormLabel width={labelWidth}>Limit</FormLabel>
            <Select
              width={selectWidth}
              options={limitOptions}
              onChange={this.onLimitChange}
              value={limitOptions.find(option => option.value === '' + limit)}
              defaultValue={'10'}
              backspaceRemovesValue
              isLoading
            />
          </div>
          <div className="gf-form col-md-6 col-sm-6">
            <FormLabel width={labelWidth}>Date</FormLabel>
            <TimePicker
              selectOptions={[
                { from: 'now-5m', to: 'now', display: 'Last 5 minutes', section: 3 },
                { from: 'now-15m', to: 'now', display: 'Last 15 minutes', section: 3 },
                { from: 'now-30m', to: 'now', display: 'Last 30 minutes', section: 3 },
                { from: 'now-1h', to: 'now', display: 'Last 1 hour', section: 3 },
                { from: 'now-3h', to: 'now', display: 'Last 3 hours', section: 3 },
                { from: 'now-6h', to: 'now', display: 'Last 6 hours', section: 3 },
                { from: 'now-12h', to: 'now', display: 'Last 12 hours', section: 3 },
                { from: 'now-24h', to: 'now', display: 'Last 24 hours', section: 3 },
              ]}
              onChange={this.onDateChange}
              value={{ from: dateTime(), to: dateTime(), raw: { from: dateTime(), to: dateTime() } }}
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
