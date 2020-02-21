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
  const generateFile = jest.spyOn(instance, 'generateFile');
  const getFileNames = jest.spyOn(instance, 'getFileNames');
  const downloadData = jest.spyOn(instance, 'downloadData')


  it('Renders correctly', () => {
      expect(wrapper).toMatchSnapshot();
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
        await instance.generateFile();
        expect(generateFile).toReturn();
  });
  
  it('getFileNames', async () => {
    await instance.getFileNames();
    //waiting for Warning: cant call setstate solution
    expect(getFileNames).toHaveBeenCalled();
  });

  it('getFile', async () => {
      await instance.getFile('');
      expect(downloadData).toHaveBeenCalled()
  });

  it('onDateChange', () => {
      const time = {
          to: dateTime(),
          from: dateTime().subtract(12, 'h'),
          raw: {
              to: 'now' as TimeFragment,
              from: 'now-12h' as TimeFragment
          }
      }
      instance.onDateChange(time)
      expect(instance.state.timeRange).toEqual(time)
  });

  it('onKeysChange', () => {
      //values
      const keys = [{value: "CavityPressure", label: "CavityPressure"}]
      instance.onKeysChange(keys)
      expect(instance.state.keys).toEqual(keys)
      //empty
      const keys_empty = []
      instance.onKeysChange(keys_empty)
      expect(instance.state.keys).toEqual(keys_empty)
      //All
      const keys_all = [{value: "All", label: "All"}]
      instance.onKeysChange(keys_all)
      expect(instance.state.keys).toEqual(instance.state.keyOptions.filter(x => x["value"] !== "All"))
  });

  it('onAnalyzersChange', () => {
      //values
      const analyzers = [{value:'AMADS3001', label: 'AMADS3001'}]
      instance.onAnalyzersChange(analyzers)
      expect(instance.state.analyzers).toEqual(analyzers)
      //empty
      const analyzers_empty = []
      instance.onAnalyzersChange(analyzers_empty)
      expect(instance.state.analyzers).toEqual(analyzers_empty)
      //All
      const analyzers_all = [{value:'All', label: 'All'}]
      instance.onAnalyzersChange(analyzers_all)
      expect(instance.state.analyzers).toEqual(instance.state.analyzerOptions.filter(x => x["value"] !== "All"))
  });

  it('onPortsChange', () => {
    //values
    const ports = [{value:'2', label: '2'}]
    instance.onPortsChange(ports)
    expect(instance.state.ports).toEqual(ports)
    //empty
    const ports_empty = []
    instance.onPortsChange(ports_empty)
    expect(instance.state.ports).toEqual(ports_empty)
    //All
    const ports_all = [{value:'All', label: 'All'}]
    instance.onPortsChange(ports_all)
    expect(instance.state.ports).toEqual(instance.state.portOptions.filter(x => x["value"] !== "All"))
   });

   it('mount with String TimeRange', () => {
    const props = {
        timeRange: {
            from: "2020-02-11T14:31:13.973Z",
            to: "2020-02-11T20:31:13.973Z",
            raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
        },
        theme: null,
        options: {
            timeRange: {
                from: dateTime("2020-02-11T14:31:13.973Z"),
                to: dateTime("2020-02-11T20:31:13.973Z"),
                raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
            }
        }
    };
    const wrap = shallow(<DataGeneratorLayout {...props}/>)
    const inst = wrap.instance() as DataGeneratorLayout
    inst.setState({
        ...inst.state.timeRange,
        timeRange: {
            from: "2020-02-11T14:31:13.973Z",
            to: "2020-02-11T20:31:13.973Z",
            raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
        }
    })
    inst.render();
    expect(inst).toMatchSnapshot();
   });

});
