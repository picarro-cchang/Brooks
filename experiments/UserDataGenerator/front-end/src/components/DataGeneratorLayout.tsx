import React, { PureComponent, Fragment } from 'react';
import { TimeRange, dateTime } from '@grafana/data';
import { TimePicker, FormLabel, PanelOptionsGroup, Select, Button } from '@grafana/ui';

import { DataGeneratorLayoutProps } from './../types';
import { DEFAULT_TIME_OPTIONS, KEYS_OPTIONS } from './../constants';

import './Layout.css';

interface Props extends DataGeneratorLayoutProps { }

const labelWidth = 6;
// @ts-ignore
const selectWidth = 12;

export default class DataGeneratorLayout extends PureComponent<Props, any> {
    constructor(props: Props) {
        super(props);
        this.state = {
            timeRange: this.props.options.timeRange
        }
    }

    generateData = () => {
        console.log('generating data...');
    }

    onDateChange = (timeRange: TimeRange) => {
        // this.props.onOptionsChange({ ...this.props.options, timeRange });
        this.setState({ timeRange });
        console.log(timeRange);
    };

    onKeysChange = (level: any) => {
        console.log(level);
        // this.props.onOptionsChange({ ...this.props.options, level: level.value })
    };

    componentWillMount() {
        console.log("Call all bootstrap apis for data");
    }

    render() {
        // @ts-ignore
        const { keys, fileName } = this.props.options;
        const { timeRange } = this.state;

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

        const fileItems = fileName.map((fn, i) => <li key={fn} className="file-item">{fn}</li>);

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
                            <Button size="md" variant="primary" value="Generate" onClick={this.generateData}>Generate</Button>
                        </div>
                    </div>

                </PanelOptionsGroup>
                <PanelOptionsGroup title="Recently Generated Files">
                    <div className="row" style={styleObj}>
                        <div className="gf-form col-md-12 col-sm-12">
                            <ul>
                                {
                                    fileItems
                                }
                            </ul>
                        </div>
                    </div>
                </PanelOptionsGroup>
            </Fragment>
        );
    }
}
