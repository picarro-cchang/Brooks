import React from 'react';
import DataGeneratorLayout from '../panels/UserDataFileGenerator/src/components/DataGeneratorLayout';
import { shallow, mount } from 'enzyme';
import { DataGeneratorLayoutProps } from '../panels/UserDataFileGenerator/src/types';
import { TimeRange, dateTime, dateMath, TimeFragment } from '@grafana/data';
import { DataGeneratorService } from '../panels/UserDataFileGenerator/src/services/DataGeneratorService'
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import "jest-fetch-mock"

// const mockClick = jest.fn((element) => {return element;});
// const apiLoc = `${window.location.hostname}:8000/controller`;
// const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: DataGeneratorLayoutProps = {
    theme: null,
    options: {
        timeRange: {
            from: dateTime("2020-02-11T14:31:13.973Z"),
            to: dateTime("2020-02-11T20:31:13.973Z"),
            raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
        }
    }
};

describe('<DataGeneratorLayout />', () => {
  const wrapper = shallow(<DataGeneratorLayout {...defaultProps}/>);
  const instance = wrapper.instance() as DataGeneratorLayout;
//   const server = new WS(socketURL);
//   const client = new WebSocket(socketURL);

  it('Renders correctly', () => {
    expect(wrapper).toMatchSnapshot();
  });
  
//   it('Generate button disabled until selections are made', () => {});

  it('generateFile functionality', () => {
      wrapper.setState({
          ...defaultProps,
          timeRange: {
              from: dateTime().subtract(6, 'h'),
              to: dateTime(),
              raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment }
          },
          keys: [{value: "WarmBoxTemp", label: "WarmBoxTemp"}],
          analyzers: [{value: "", label: ""}],
          ports: [{value: "", label: ""}]
      });
      console.log(wrapper.state())
  });
  
});

