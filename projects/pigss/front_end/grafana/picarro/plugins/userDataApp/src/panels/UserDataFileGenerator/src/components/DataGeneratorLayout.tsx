import React, { PureComponent, Fragment } from 'react';
import { TimeRange, TIME_FORMAT, dateTime, dateMath } from '@grafana/data';
import { TimePicker, FormLabel, PanelOptionsGroup, Select, Button } from '@grafana/ui';

import { notifyError, notifySuccess } from '../utils/Notifications';
import { DataGeneratorLayoutProps } from '../types';
import { DEFAULT_TIME_OPTIONS } from '../constants';
import { DataGeneratorService } from '../services/DataGeneratorService';

import './Layout.css';

interface Props extends DataGeneratorLayoutProps { }

const labelWidth_6 = 6;
const labelWidth_7 = 7;
const selectWidth = 12;

export default class DataGeneratorLayout extends PureComponent<Props, any> {
  constructor(props: Props) {
    super(props);
    this.state = {
      timeRange: this.props.options.timeRange,
      keys: [],
      keyOptions: [],
      files: [],
    };
  }

  // Code to download the file
  downloadData = (blob: any, fileName: string) => {
    const a = document.createElement('a');

    document.getElementById('file-list').appendChild(a);
    // @ts-ignore
    a.style = 'display: none';
    const url = window.URL.createObjectURL(blob);
    a.href = url;
    a.download = fileName;
    a.click();
    notifySuccess(`File successfully downloaded in Downloads folder.`);
    window.URL.revokeObjectURL(url);
  };

  generateFile = () => {
    const { timeRange, keys } = this.state;
    const {from, to } = {
      from: dateMath.parse(timeRange.raw.from),
      to: dateMath.parse(timeRange.raw.to),
      raw: timeRange.raw
    } as TimeRange;
    
    // @ts-ignore
    let fromTime = from._d.getTime();
    // @ts-ignore
    let toTime = to._d.getTime();

    if (fromTime === toTime || keys.length === 0) {
      notifyError('Invalid Query parameters');
      return;
    }

    const queryParams = {
      from: fromTime * 1000000,
      to: toTime * 1000000,
      keys: keys,
    };

    // Call generate file api
    DataGeneratorService.generateFile(queryParams).then((response: any) => {
      response.json().then((data: any) => {
        // call getFile to download the data
        if (data.filename !== undefined) {
          this.getFileNames();
          this.getFile(data.filename);
        } else {
          if (data !== undefined && data.hasOwnProperty('message')) {
            notifyError(data.message);
          }
        }
      });
    });
  };

  getFile = (fileName: string) => {
    DataGeneratorService.getFile(fileName).then((response: any) => {
      response.blob().then((data: any) => {
        this.downloadData(data, fileName);
      });
    });
  };

  getFileNames = () => {
    // Get file names
    DataGeneratorService.getSavedFiles().then((response: any) => {
      response.json().then((files: any) => {
        this.setState(() => {
          return files;
        });
      });
    });
  };

  onDateChange = (timeRange: TimeRange) => {
    this.setState({ timeRange });
  };

  onKeysChange = (keys: any) => {
    this.setState(() => {
      return { keys };
    });
  };

  componentWillMount() {
    // Get file names
    this.getFileNames();

    // Get Key Options
    DataGeneratorService.getKeys().then((response: any) => {
      response.json().then((data: any) => {
        const keyOptions = data.keys.map((x: string) => {
          return {
            value: x,
            label: x,
          };
        });
        this.setState({ keyOptions: keyOptions });
      });
    });
  }

  render() {
    const { files, timeRange, keyOptions } = this.state;

    const styleObj = {
      overflow: 'scroll !important',
      height: 'inherit',
    };

    if (typeof timeRange.from === 'string') {
      timeRange.from = dateTime(timeRange.from);
    }
    if (typeof timeRange.to === 'string') {
      timeRange.to = dateTime(timeRange.to);
    }

    const fileItems = files.map((fn: string, i: number) => {
      return (
        <li key={fn} className="file-item" value={fn} onClick={() => this.getFile(fn)}>
          {fn}
        </li>
      );
    });

    return (
      <Fragment>
        <h3 className="text-center">User Data File Generator</h3>
        <PanelOptionsGroup title="Generate New File">
          <div className="row">
            <div className="gf-form col-md-3 col-sm-12">
              <FormLabel width={labelWidth_6}>Species</FormLabel>
              <Select
                width={selectWidth}
                options={keyOptions}
                onChange={this.onKeysChange}
                value={keyOptions.find((option: any) => option.value === 'key')}
                isMulti={true}
                backspaceRemovesValue
              />
            </div>
            <div className="gf-form col-md-6 col-sm-12 time-picker-container">
              <FormLabel width={labelWidth_7}>Time Range</FormLabel>
              <TimePicker
                timeZone="browser"
                selectOptions={DEFAULT_TIME_OPTIONS}
                onChange={this.onDateChange}
                value={this.state.timeRange}
                onMoveBackward={() => console.log('Move Backward')}
                onMoveForward={() => console.log('Move forward')}
                onZoom={() => console.log('Zoom')}
              />
            </div>

            <div className="gf-form col-md-3 col-sm-12">
              <Button size="md" variant="primary" value="Generate" onClick={this.generateFile} disabled={!this.state.keys.length}>
                Generate
              </Button>
            </div>
          </div>
        </PanelOptionsGroup>
        <PanelOptionsGroup title="Recently Generated Files">
          <div className="row" style={styleObj}>
            <div className="gf-form col-md-12 col-sm-12">
              <ul id="file-list" style={{ listStyle: 'none' }}>
                {fileItems}
              </ul>
            </div>
          </div>
        </PanelOptionsGroup>
      </Fragment>
    );
  }
}
