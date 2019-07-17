import React, { PureComponent } from "react";
import { PanelProps, getTheme } from "@grafana/ui";
import { Options } from "../types";
import { MFCLayout } from "./MFCLayout";

interface Props extends PanelProps<Options> {}


export class MFCPanel extends PureComponent<Props> {
  render() {
    const { options } = this.props;

    return (
        <div>
          <MFCLayout options={options}/>
        </div>
    );
  }
}
