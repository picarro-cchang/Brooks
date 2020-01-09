import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import Modal from 'react-responsive-modal';
import WS from 'jest-websocket-mock';
import {Main} from '../Main';
import PicarroAPI from '../../api/PicarroAPI';
import 'jest-fetch-mock';
import {PlanPanelTypes} from '../../types';
import PlanPanel from '../PlanPanel';

const defaultState = {
    initialized: false,
    modal_info: {
      show: false,
      html: "",
      num_buttons: 0,
      buttons: {}
    },
    uistatus: {},
    plan: {
      max_steps: 10,
      panel_to_show: 0,
      current_step: 1,
      focus: { row: 0, column: 0 },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: {
        1: {
          name: "Bank 1",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8"
          }
        },
        2: {
          name: "Bank 2",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8"
          }
        },
        3: {
          name: "Bank 3",
          channels: {
            1: "Channel",
            2: "Channel",
            3: "Channel",
            4: "Channel",
            5: "Channel",
            6: "Channel",
            7: "Channel",
            8: "Channel"
          }
        },
        4: {
          name: "Bank 4",
          channels: {
            1: "Channel",
            2: "Channel",
            3: "Channel",
            4: "Channel",
            5: "Channel",
            6: "Channel",
            7: "Channel",
            8: "Channel"
          }
        }
      }
    },
    options: {
      panel_to_show: 0
    },
    isPlan: false,
    isChanged: false
  };

  const defaultState1 = {
    initialized: false,
    modal_info: {
      show: false,
      html: "",
      num_buttons: 0,
      buttons: {}
    },
    uistatus: {},
    plan: {
      max_steps: 10,
      panel_to_show: 0,
      current_step: 1,
      focus: { row: 0, column: 0 },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: {
        1: {
          name: "Bank 1",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8"
          }
        },
        2: {
          name: "Bank 2",
          channels: {
            1: "Channel 1",
            2: "Channel 2",
            3: "Channel 3",
            4: "Channel 4",
            5: "Channel 5",
            6: "Channel 6",
            7: "Channel 7",
            8: "Channel 8"
          }
        },
        3: {
          name: "Bank 3",
          channels: {
            1: "Channel",
            2: "Channel",
            3: "Channel",
            4: "Channel",
            5: "Channel",
            6: "Channel",
            7: "Channel",
            8: "Channel"
          }
        },
        4: {
          name: "Bank 4",
          channels: {
            1: "Channel",
            2: "Channel",
            3: "Channel",
            4: "Channel",
            5: "Channel",
            6: "Channel",
            7: "Channel",
            8: "Channel"
          }
        }
      }
    },
    options: {
      panel_to_show: 0
    },
    isPlan: false,
    isChanged: false
  };

describe('<Main />', () => {
    const wrapper = mount(<Main />);
    wrapper.setState({...defaultState});
    const instance = wrapper.instance() as Main;

    it('Snapshot', () => {
        expect(wrapper).toMatchSnapshot();
    });

    it('Check correct left panel is showing', () => {
        expect(wrapper.state()["plan"].panel_to_show).toEqual(0);
        expect(PlanPanelTypes.NONE).toEqual(wrapper.state()["plan"].panel_to_show);
        // wrapper.setState({
        //   ...defaultState,
        //   plan: {
        //     panel_to_show: 1
        //   }
        // });
        // expect(wrapper.state()["plan"].panel_to_show).toEqual(1);
        // expect(PlanPanelTypes.PLAN).toEqual(wrapper.state()["plan"].panel_to_show);
        // expect(wrapper).toMatchSnapshot();
        wrapper.setState({
          ...defaultState,
          plan: {
            panel_to_show: 2
          }
        });
        expect(wrapper.state()["plan"].panel_to_show).toEqual(2);
        wrapper.setState({
          ...defaultState,
          plan: {
            panel_to_show: 3
          }
        });
        expect(wrapper.state()["plan"].panel_to_show).toEqual(3);
        wrapper.setState({
          ...defaultState,
          plan: {
            panel_to_show: 4
          }
        });
        expect(wrapper.state()["plan"].panel_to_show).toEqual(4);
        wrapper.setState({
          ...defaultState,
          plan: {
            panel_to_show: 0
          }
        });
    });

    it('API test', () => {

    });

    it('handleData', () => {

    });

    it('WS', () => {

    });

    it('updateFileName', () => {
        instance.updateFileName.call(defaultState, true);
        // expect(instance.state.isChanged).toEqual(true);
        instance.updateFileName.call(defaultState, false);
    });

    it('Modal', () => {

    });

    it('Check banks render', () => {

    });
});
