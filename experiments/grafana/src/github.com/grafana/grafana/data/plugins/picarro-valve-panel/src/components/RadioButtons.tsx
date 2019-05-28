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
      <div
        key={ndx.toString()}
        style={{ display: 'inline-block', width: '80px' }}
      >
        <label>
          <input
            type="radio"
            name={name}
            id={name + '-' + (firstIndex + ndx)}
            value={
              valueField
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
  selectedIndex?: number;
  selectedValue?: string;
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
  }

  onRowChange(e: any) {
    const selectedIndex = Number(e.target.id.split('-')[1]);
    if (this.props.onChange) {
      const datum = this.props.data[selectedIndex];
      const { textField } = this.props;
      const selectedText = textField
        ? typeof textField === 'string'
          ? datum[textField]
          : textField(datum)
        : datum;
      this.props.onChange({
        selectedIndex,
        selectedValue: e.target.value,
        selectedText,
      });
    }
  }

  render() {
    const {
      name,
      data,
      textField,
      valueField,
      perRow,
      selectedIndex,
      selectedValue,
    } = this.props;
    let i: number, j: number;
    let items: ReactNode[] = [];
    let ndx = selectedIndex;
    if (selectedIndex == null && !(selectedValue == null)) {
      data.forEach((datum, i) => {
        const value: string = valueField
          ? typeof valueField === 'string'
            ? datum[valueField]
            : valueField(datum)
          : datum;
        if (String(value) === String(selectedValue)) {
          ndx = i;
        }
      });
    }
    for (i = 0; i < data.length; i += perRow) {
      let rowData: string[] = [];
      for (j = i; j < i + perRow && j < data.length; j++) {
        rowData.push(data[j]);
      }
      items.push(
        <RadioButtonRow
          key={i.toString()}
          name={name}
          data={rowData}
          textField={textField}
          valueField={valueField}
          firstIndex={i}
          selectedIndex={ndx}
          onChange={e => this.onRowChange(e)}
        />
      );
    }
    return items;
  }
}
