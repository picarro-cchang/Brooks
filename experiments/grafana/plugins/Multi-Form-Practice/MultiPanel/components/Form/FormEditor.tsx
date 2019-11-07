import React, { PureComponent } from "react";
import {Select, PanelOptionsGroup, PanelEditorProps, FormField, FormLabel, PanelOptionsGrid} from "@grafana/ui";
import { Options } from "../../types";
// import {LayoutOptions} from "./LayoutOptions";
// import {SingleStatValueOptions} from "../../../../combo-panel/Hello-Editor/types";

interface Props {
    options: Options;
    onChange: (formOptions: Options) => void;
}

/*interface State {
  fName: string;
  lName: string;
  age: number;
  gender: string;
  imageUrl: string;
}*/


const labelWidth = 4;
const statOptions = [
    { value: 'Gender', label: 'Gender' },
    { value: 'Male', label: 'Male' },
    { value: 'Female', label: 'Female' }
];

export class FormEditor extends PureComponent<Props> {

    onTextChange = ({ target }) =>
        this.props.onChange({
            ...this.props.options,
            [target.name] : target.value,
        });
    onGenderChange = gender =>
        this.props.onChange({ ...this.props.options, gender: gender.value });


  render() {
      const { options } = this.props;
      const { fName, lName, age, gender, imageUrl } = options;

    return (
          <PanelOptionsGroup title="Form">
            <div className="gf-form">
              <FormField
                  name="fName"
                  label="First Name"
                  labelWidth={12}
                  inputWidth={25}
                  value={fName}
                  onChange={this.onTextChange}
              />
            </div>
              <div className="gf-form">
                  <FormField
                      name="lName"
                      label="Last Name"
                      labelWidth={12}
                      inputWidth={25}
                      value={lName}
                      onChange={this.onTextChange}
                  />
              </div>
              <div className="gf-form">
                  <FormField
                      name="age"
                      label="Age"
                      labelWidth={12}
                      inputWidth={25}
                      value={age}
                      onChange={this.onTextChange}
                  />
              </div>
              <div>
                  <FormLabel width={labelWidth}>Name</FormLabel>
                  <Select //need to get this inline with FormLabel
                      width={8}
                      options={statOptions}
                      onChange={this.onGenderChange}
                      value={statOptions.find(option => option.value === gender)}
                      defaultValue={'Gender'}
                      backspaceRemovesValue isLoading/>
              </div>
              <div className="gf-form">
                  <FormField
                      name="imageUrl"
                      label="Image URL"
                      labelWidth={12}
                      inputWidth={25}
                      value={imageUrl}
                      onChange={this.onTextChange}
                  />
              </div>
          </PanelOptionsGroup>
    );

  }
}
