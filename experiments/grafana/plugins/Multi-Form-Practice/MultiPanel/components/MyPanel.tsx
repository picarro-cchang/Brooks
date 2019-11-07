import React, { PureComponent } from "react";
import { PanelProps } from "@grafana/ui";
import { ExtraOptions } from "../types";
import { FormLayout } from "./Form/FormLayout";

// interface Props extends PanelProps<Options> {}

interface Props extends PanelProps<ExtraOptions> {}


export class MyPanel extends PureComponent<Props> {

    render() {
        const {options} = this.props;
        const {layout} = options;


        switch (layout) {
            case 'bigform':
                return (
                    <FormLayout options={options}/>
                );

            case 'bigtext':
                return (
                    <div>Hello</div>
                );
        }
    }
}
