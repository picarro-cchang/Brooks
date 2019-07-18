import React, { PureComponent} from 'react';
import {MyProps} from "../types";
import {FormField} from "@grafana/ui";

export interface Props extends MyProps {}

export class MFCLayout extends PureComponent<Props> {
  render() {
    const {options} = this.props;
    const {flowRate, setPoint} = options;
    return (
        <div>
            <br/>
          <FormField label="Flow Rate: " value={flowRate} readOnly />
          <FormField label="Set Point: " value={setPoint} readOnly />
        </div>
    );
  }
}
