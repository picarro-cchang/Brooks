import React, { PureComponent } from "react";
import {Select, PanelOptionsGroup, PanelEditorProps, FormField, FormLabel, PanelOptionsGrid} from "@grafana/ui";
import { ExtraOptions, Options } from "../types";
import {LayoutOptions} from "./LayoutOptions";
import {FormEditor} from "./Form/FormEditor";

/*interface State {
  fName: string;
  lName: string;
  age: number;
  gender: string;
  imageUrl: string;
}*/

// const labelWidth = 4;
// const statOptions = [
//     { value: 'Gender', label: 'Gender' },
//     { value: 'Male', label: 'Male' },
//     { value: 'Female', label: 'Female' }
// ];

export class MyPanelEditor extends PureComponent<
    PanelEditorProps<ExtraOptions>> {

    // onTextChange = ({ target }) =>
    //     this.props.onChange({
    //         ...this.props.options,
    //         [target.name] : target.value,
    //     });
    onValueOptionsChanged = (formOptions: Options) =>
        this.props.onChange({
            ...this.props.options,
            formOptions,
        });
    // onGenderChange = gender =>
    //     this.props.onChange({ ...this.props.options, gender: gender.value });
    //
    onLayoutChange = layout =>
        this.props.onChange({ ...this.props.options, layout: layout });

  render() {
      const { options } = this.props;
      // const { layout, fName, lName, age, gender, imageUrl } = options;
      const { layout, formOptions } = options;


      return (

        <>
            <PanelOptionsGrid>
                <LayoutOptions
                    onChange={layout => this.onLayoutChange(layout)}
                    selectedLayout={layout}
                />
            </PanelOptionsGrid>
            <PanelOptionsGrid>
                <FormEditor
                    options={formOptions}
                    onChange={valueOptions => this.onValueOptionsChanged(valueOptions)}
                    />
            </PanelOptionsGrid>
        </>
    );

  }
}
