import React, { Component } from 'react';
import Select, { components } from 'react-select';

const customStyles = {
  container: provided => ({
    ...provided,
    minWidth: '10%',
  }),
  menu: provided => ({
    ...provided,
    padding: 5,
    backgroundColor: '#262628',
  }),
  option: provided => ({
    ...provided,
    color: '#d8d9da',
    backgroundColor: '#262628',
  }),
  control: provided => ({
    ...provided,
    color: '#d8d9da',
    backgroundColor: '#09090b',
    border: '1px solid #262628',
  }),
  multiValue: provided => ({
    ...provided,
    color: '#d8d9da',
    fontSize: 14,
    backgroundColor: '#09090b',
  }),
  multiValueLabel: provided => ({
    ...provided,
    color: '#d8d9da',
    fontSize: 14,
    backgroundColor: '#09090b',
  }),
};

const Option = props => {
  return (
    <div style={{ display: 'flex' }}>
      <components.Option {...props}>
        <label>
          <input type="checkbox" checked={props.isSelected} onChange={e => null} />
          <span className="checkbox-label">
            {'   '}
            {props.value}
          </span>
        </label>
      </components.Option>
    </div>
  );
};

const ClearIndicator = props => {
  return null;
};

export interface Props {
  passedOptions: [];
  passedOnChange: (keys: any) => void;
  allOption: {
    label: string;
    value: string;
  };
  value: [];
}

export default class CustomSelect extends Component<Props> {
  constructor(props) {
    super(props);
  }
  render() {
    const { passedOptions, passedOnChange, value } = this.props;
    return (
      <Select
        placeholder="Select..."
        components={{ Option, ClearIndicator }}
        styles={customStyles}
        options={passedOptions}
        onChange={passedOnChange}
        value={value}
        // value={passedOptions.find((option: any) => option.value === 'key')}
        isMulti={true}
        closeMenuOnSelect={false}
        hideSelectedOptions={false}
        backspaceRemovesValue={true}
      />
    );
  }
}
