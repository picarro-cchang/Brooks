import React, { PureComponent, Fragment } from 'react';
import { TimeRange, dateTime } from '@grafana/data';
import { TimePicker, FormLabel, PanelOptionsGroup, Select, Button } from '@grafana/ui';

import { DataGeneratorLayoutProps } from './../types';
import { DEFAULT_TIME_OPTIONS, KEYS_OPTIONS, DEFAULT_TIME_RANGE } from './../constants';

import { DataGeneratorService } from '../services/DataGeneratorService';

import './Layout.css';

interface Props extends DataGeneratorLayoutProps { }

const labelWidth = 6;
// @ts-ignore
const selectWidth = 12;

export default class DataGeneratorLayout extends PureComponent<Props, any> {
    constructor(props: Props) {
        super(props);
        this.state = {
            timeRange: DEFAULT_TIME_RANGE,
            keys: [],
            files: [],
        };
    }

    // Code to download the file
    downloadData = (blob: any, fileName: string) => {
        const a = document.createElement("a");
        // @ts-ignore
        document.getElementById("file-list").appendChild(a);
        // @ts-ignore
        a.style = "display: none";

        const url = window.URL.createObjectURL(blob);
        a.href = url;
        a.download = fileName;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    generateData = () => {
        console.log('generating data...');
        console.log('Current State for generate', this.state);
    };

    getFile = (fileName: string) => {
        DataGeneratorService.getFile(fileName).then(response => {
            response.blob().then(data => {
                this.downloadData(data, fileName);
            });
        });
    }

    onDateChange = (timeRange: TimeRange) => {
        this.setState({ timeRange });
    };

    onKeysChange = (keys: any) => {
        this.setState({ keys });
    };

    componentWillMount() {
        console.log('Call all bootstrap apis for data'); //  KEY_OPTIONS, FILE NAMES

        // Get file names
        DataGeneratorService.getSavedFiles().then(response => {
            response.json().then(files => {
                this.setState(() => {
                    return files;
                });
            })
        });

        // Get Key Options
    }

    render() {
        // @ts-ignore
        const { keys, files, timeRange } = this.state;

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

        const fileItems = files.map((fn: string) => (
            <li key={fn} className="file-item" value={fn} onClick={() => this.getFile(fn)}>
                {fn}
            </li>
        ));

        return (
            <Fragment>
                <h3 className="text-center">User Data File Generator</h3>
                <PanelOptionsGroup title="Generate New File">
                    <div className="row">
                        <div className="gf-form col-md-3 col-sm-12">
                            <FormLabel width={labelWidth}>Keys</FormLabel>
                            <Select
                                width={selectWidth}
                                options={KEYS_OPTIONS}
                                onChange={this.onKeysChange}
                                value={KEYS_OPTIONS.find(option => option.value === 'key')}
                                isMulti={true}
                                backspaceRemovesValue
                                isLoading
                            />
                        </div>
                        <div className="gf-form col-md-6 col-sm-12">
                            <FormLabel width={labelWidth}>Date</FormLabel>
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
                            <Button size="md" variant="primary" value="Generate" onClick={this.generateData}>
                                Generate
              </Button>
                        </div>
                    </div>
                </PanelOptionsGroup>
                <PanelOptionsGroup title="Recently Generated Files">
                    <div className="row" style={styleObj}>
                        <div className="gf-form col-md-12 col-sm-12">
                            <ul id="file-list" style={{ "display": "inherit" }}>{fileItems}</ul>
                        </div>
                    </div>
                </PanelOptionsGroup>
            </Fragment >
        );
    }
}
