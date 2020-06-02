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
  option: (provided, state) => ({
    ...provided,
    color: '#d8d9da',
    backgroundColor: state.isFocused ? '#44484a' : '#262628',
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
        <div className="checkbox-div">
          <input className="check-input" type="checkbox" checked={props.isSelected} onChange={e => null} />
          <label className="checkbox-label">
            <span className="checkbox-span">
              <span className="checkbox-name">
                {'   '}
                {props.value}
              </span>
            </span>
          </label>
        </div>
      </components.Option>
    </div>
  );
};

const ClearIndicator = props => {
  return null;
};

const MultiValue = props => {
  const labelToBeDisplayed = `${props.data.label}`;
  return (
    <components.MultiValue {...props}>
      <span>{labelToBeDisplayed}</span>
    </components.MultiValue>
  );
};

export interface Props {
  passedOptions: any[];
  passedOnChange: (keys: any) => void;
  allOption: {
    label: string;
    value: string;
  };
  value: any[];
}

export default class CustomSelect extends Component<Props> {
  constructor(props) {
    super(props);
  }
  render() {
    const { passedOptions, passedOnChange } = this.props;
    return (
      <Select
        {...this.props}
        classNamePrefix="list"
        placeholder="Select..."
        components={{ Option, ClearIndicator, MultiValue }}
        styles={customStyles}
        options={passedOptions}
        onChange={passedOnChange}
        value={passedOptions.find((option: any) => option.value === 'key')}
        isMulti={true}
        closeMenuOnSelect={false}
        hideSelectedOptions={false}
        backspaceRemovesValue={true}
      />
    );
  }
}
