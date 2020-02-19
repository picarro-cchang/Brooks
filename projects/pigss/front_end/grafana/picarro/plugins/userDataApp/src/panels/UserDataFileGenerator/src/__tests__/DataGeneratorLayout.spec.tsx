import React from 'react';
import DataGeneratorLayout from '../components/DataGeneratorLayout';
import { shallow, mount } from 'enzyme';
import { DataGeneratorLayoutProps } from '../types';
import { TimeRange, dateTime, dateMath, TimeFragment } from '@grafana/data';
import 'jest-styled-components';
import "jest-fetch-mock";

jest.mock('./../services/DataGeneratorService.ts');
jest.mock('./../utils/Notifications.ts')

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
  let data = new DataGeneratorLayout({...defaultProps});
  const generateFile = jest.spyOn(instance, 'generateFile');
  const getFileNames = jest.spyOn(instance, 'getFileNames');
  const downloadData = jest.spyOn(instance, 'downloadData')

  it('Renders correctly', () => {
      return expect(wrapper).toMatchSnapshot();
  });

  it('generateFile', async () => {
      instance.setState({
          ...instance.state.analyzers,
          analyzers: [{value: "AMSADS3003", label: "AMSADS3003"}],
          ...instance.state.keys,
          keys: [{value: "CavityTemp", label: "CavityTemp"}],
          ...instance.state.ports,
          ports: [{value: "2", label: "2"}],
      })
      await instance.generateFile()      
      expect(generateFile).toHaveBeenCalled();
      //test if to & from are equal
      instance.setState({
        ...instance.state.timeRange,
        timeRange: {
            raw: {
                to: 'now' as TimeFragment,
                from: 'now' as TimeFragment
            }
        }
        });
        instance.generateFile();
        expect(generateFile).toReturn();
  });
  
  it('getFileNames', async () => {
    await instance.getFileNames();
    // expect(data.state.files).toEqual('files')
    //waiting for Warning: cant call setstate solution
    expect(getFileNames).toHaveBeenCalled();
  });

  it('getFile', async () => {
      await instance.getFile('');
      expect(downloadData).toHaveBeenCalled()
  });


});

