import React, { PureComponent} from 'react';
import {MyProps} from "../types";
import {FormField} from "@grafana/ui";


export interface Props extends MyProps {}



export class MFCLayout extends PureComponent<Props> {

    render() {
        const {options} = this.props;
        const {flow_rate, set_point} = options;

        return (
            <div>
                <br/>
                <FormField label="Flow Rate: " value={flow_rate} readOnly/>
                <FormField label="Set Point: " value={set_point} readOnly/>
            </div>
        );
    }
}
