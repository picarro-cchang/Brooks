// import React, { PureComponent } from 'react';
// import DataGeneratorLayout from '../components/DataGeneratorLayout';
// import { shallow, mount } from 'enzyme';
// import { DataGeneratorLayoutProps } from '../types';
// import { TimeRange, dateTime, dateMath, TimeFragment } from '@grafana/data';
// // import { DataGeneratorService } from '../services/__mocks__/DataGeneratorService'
// import 'jest-styled-components';
// import "jest-fetch-mock"

// // const mockgetFile = jest.fn((fileName) => {return fileName;});
// // const apiLoc = `${window.location.hostname}:8000/controller`;
// // const socketURL = `ws://${apiLoc}/ws`;


// const defaultProps: DataGeneratorLayoutProps = {
//     theme: null,
//     options: {
//         timeRange: {
//             from: dateTime("2020-02-11T14:31:13.973Z"),
//             to: dateTime("2020-02-11T20:31:13.973Z"),
//             raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment },
//         }
//     }
// };

// describe('<DataGeneratorLayout />', () => {
//   const wrapper = shallow(<DataGeneratorLayout {...defaultProps}/>);
//   // const instance = wrapper.instance() as DataGeneratorLayout;
// //   const server = new WS(socketURL);
// //   const client = new WebSocket(socketURL);

//   it('Renders correctly', () => {
//     expect(wrapper).toMatchSnapshot();
//   });
  
// //   it('Generate button disabled until selections are made', () => {});

//   // it('DataService generateFile functionality', () => {
//       // wrapper.setState({
//       //     ...defaultProps,
//       //     timeRange: {
//       //         from: dateTime().subtract(6, 'h'),
//       //         to: dateTime(),
//       //         raw: { from: 'now-6h' as TimeFragment, to: 'now' as TimeFragment }
//       //     },
//       //     keys: [{value: "WarmBoxTemp", label: "WarmBoxTemp"}],
//       //     analyzers: [{value: "AMADS3001", label: "AMADS3001"}],
//       //     ports: [{value: "All", label: "All"}]
//       // });
//       // const { from, to } = {
//       //   from: dateMath.parse(wrapper.state()["timeRange"].raw.from),
//       //   to: dateMath.parse(wrapper.state()["timeRange"].raw.to),
//       //   raw: wrapper.state()["timeRange"].raw
//       // } as TimeRange;
//       // // @ts-ignore
//       // let fromTime = from._d.getTime();

//       // // @ts-ignore
//       // let toTime = to._d.getTime();

//       // const queryParams = {
//       //   ports: wrapper.state()["ports"],
//       //   from: fromTime * 1000000,
//       //   to: toTime * 1000000,
//       //   keys: wrapper.state()["keys"],
//       //   analyzers: wrapper.state()["analyzers"]
//       // };

//       // // return DataGeneratorService.generateFile(queryParams).then(response => {
//       // //   expect(response).toEqual({"filename": "picarro-02-12-2020_095753-02-12-2020_155753.csv"})
//       // // })

// // });
// });

// //{"filename": "picarro-02-12-2020_095753-02-12-2020_155753.csv"}