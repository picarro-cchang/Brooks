import React from 'react';
import DataGeneratorLayout from '../components/DataGeneratorLayout';
import { shallow, mount } from 'enzyme';
import { DataGeneratorLayoutProps } from '../types';
import { TimeRange, dateTime, dateMath, TimeFragment } from '@grafana/data';
import 'jest-styled-components';
import "jest-fetch-mock";
import { API } from '../services/API';

jest.mock('./../services/DataGeneratorService.ts');

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
  const getFileNames = jest.spyOn(instance, 'getFileNames');

  it('Renders correctly', () => {
      return expect(wrapper).toMatchSnapshot();
  });

  it('generateFile', () => {
      const generateFile = jest.spyOn(instance, 'generateFile');
      instance.forceUpdate();
      instance.generateFile()      
      expect(generateFile).toHaveBeenCalled();
  });
  
  it('getFileNames', async () => {
      await instance.getFileNames();
      expect(getFileNames).toHaveBeenCalled();
      await expect(instance.state.files).toEqual('files')
  });
});

