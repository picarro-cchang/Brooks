import React, { Component, PureComponent, ReactNode } from 'react';

type AnyToString = (datum: any) => string;

interface RadioButtonRowProps {
  name: string;
  data: any[];
  textField?: string | AnyToString;
  valueField?: string | AnyToString;
  firstIndex: number;
  selectedIndex: number;
  onChange(e: any): void;
}

class RadioButtonRow extends PureComponent<RadioButtonRowProps> {
  render() {
    const {
      name,
      data,
      textField,
      valueField,
      firstIndex,
      selectedIndex,
    } = this.props;
    const listItems = data.map((datum, ndx) => (
      <div style={{ display: 'inline-block', width: '80px' }}>
        <label>
          <input
            type="radio"
            name={name}
            id={name + '-' + (firstIndex + ndx)}
            value={
              textField
                ? typeof valueField === 'string'
                  ? datum[valueField]
                  : valueField(datum)
                : datum
            }
            checked={firstIndex + ndx == selectedIndex}
            onChange={e => this.props.onChange(e)}
          />
          {textField
            ? typeof textField === 'string'
              ? datum[textField]
              : textField(datum)
            : datum}
        </label>
      </div>
    ));
    return <div>{listItems}</div>;
  }
}

interface RadioButtonBlockProps {
  name: string;
  data: any[];
  textField?: string | AnyToString;
  valueField?: string | AnyToString;
  perRow: number;
  onChange?(e: any): void;
}

interface RadioButtonBlockState {
  selectedIndex: number;
}

export default class RadioButtonBlock extends Component<
  RadioButtonBlockProps,
  RadioButtonBlockState
> {
  constructor(props: RadioButtonBlockProps) {
    super(props);
    this.state = { selectedIndex: 0 };
  }

  onRowChange(e: any) {
    this.setState({ selectedIndex: Number(e.target.id.split('-')[1]) });
    if (this.props.onChange) {
      this.props.onChange(e);
    }
  }

  render() {
    const { name, data, textField, valueField, perRow } = this.props;
    let i: number, j: number;
    let items: ReactNode[] = [];
    for (i = 0; i < data.length; i += perRow) {
      let rowData: string[] = [];
      for (j = i; j < i + perRow && j < data.length; j++) {
        rowData.push(data[j]);
      }
      items.push(
        <RadioButtonRow
          name={name}
          data={rowData}
          textField={textField}
          valueField={valueField}
          firstIndex={i}
          selectedIndex={this.state.selectedIndex}
          onChange={e => this.onRowChange(e)}
        />
      );
    }
    return items;
  }
}
