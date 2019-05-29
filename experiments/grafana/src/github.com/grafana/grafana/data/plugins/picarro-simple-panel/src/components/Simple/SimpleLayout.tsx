import React, { Component } from 'react';

import { LayoutProps } from '../../types';
import PicarroAPI from '../../api/PicarroAPI';
import RadioButtons from '../RadioButtons/RadioButtons';
import IntervalRenderer from 'react-interval-renderer';

interface Props extends LayoutProps {}

export class SimpleLayout extends Component<Props, any> {
  constructor(props) {
    super(props);
    this.state = { message: 'None' };
  }

  onButtonClick(e: any) {
    PicarroAPI.getRequest('http://numbersapi.com/random/trivia').then(
      response => {
        response.text().then(text => {
          this.setState({ message: text });
          PicarroAPI.postData('http://localhost:8888/print', {
            message: text,
          }).then(response => {
            response.text().then(text => {
              console.log(text);
            });
          });
        });
      }
    );
  }

  onValveChange(e: any) {
    PicarroAPI.postData('http://localhost:8888/valve_mode', {
      mode: e.target.value,
    }).then(response => {
      response.text().then(text => {
        console.log(text);
      });
    });
  }

  render() {
    const { height, width, theme, options, onInterpolate } = this.props;
    const { minValue, maxValue, textValue } = options;
    const data = [
      { value: -1, text: 'Scan' },
      { value: 0, text: 'Valve 0' },
      { value: 1, text: 'Valve 1' },
      { value: 2, text: 'Valve 2' },
      { value: 3, text: 'Valve 3' },
      { value: 4, text: 'Valve 4' },
      { value: 5, text: 'Valve 5' },
      { value: 6, text: 'Valve 6' },
      { value: 7, text: 'Valve 7' },
      { value: 8, text: 'Valve 8' },
      { value: 9, text: 'Valve 9' },
      { value: 10, text: 'Valve 10' },
      { value: 11, text: 'Valve 11' },
      { value: 12, text: 'Valve 12' },
      { value: 13, text: 'Valve 13' },
      { value: 14, text: 'Valve 14' },
      { value: 15, text: 'Valve 15' },
    ];
    return (
      <div>
        <div
          style={{
            display: 'flex',
            width: '100%',
            height: '100%',
            flexDirection: 'column',
          }}
        />
        <div>
          <h1>Parameter values</h1>
          <div>Minimum = {minValue}</div>
          <div>Maximum = {maxValue}</div>
          <div>Text = {onInterpolate(textValue)}</div>
          <div>Height = {height}</div>
          <div>Width = {width}</div>
          <div>Theme = {theme.type}</div>
          <button
            className="btn btn-primary btn-large"
            onClick={e => this.onButtonClick(e)}
          >
            Click Me
          </button>
          <div>Message = {this.state.message}</div>
        </div>
        <IntervalRenderer interval={1000}>
          <RadioButtons
            name="opt"
            data={data}
            perRow={4}
            valueField={'value'}
            textField={'text'}
            onChange={e => this.onValveChange(e)}
          />
        </IntervalRenderer>
      </div>
    );
  }
}
