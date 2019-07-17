import React, { PureComponent} from 'react';
import {MyProps} from "../types";
import {FormField, FormLabel} from "@grafana/ui";

export interface Props extends MyProps {}

export class MFCLayout extends PureComponent<Props> {
  render() {
    const {options} = this.props;
    const {flowRate, setPoint} = options;
    return (
        <div>
          <FormField label="Flow Rate: " value={flowRate}/>
          <FormField label="Set Point: " value={setPoint}/>
        </div>
    );
  }
}
