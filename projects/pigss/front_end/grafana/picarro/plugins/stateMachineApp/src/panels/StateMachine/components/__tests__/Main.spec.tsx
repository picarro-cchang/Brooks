import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import Modal from 'react-responsive-modal';
import WS from 'jest-websocket-mock';
import {Main} from '../Main';
import PicarroAPI from '../../api/PicarroAPI';
import 'jest-fetch-mock';
import {PlanPanelTypes} from '../../types';
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import {notifyError, notifySuccess} from '../../utils/Notifications';

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
      panel_to_show: 1,
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
    isPlan: true,
    isChanged: false
  };

  const uistatus = {
    initialized: true,
    uistatus: {
      bank: {"1": "READY", "3": "READY", "4": "READY"}, 
      channel: {
        "1": {"1": "DISABLED", "2": "AVAILABLE", "3": "DISABLED", "4": "AVAILABLE", "5": "DISABLED", "6": "AVAILABLE", "7": "DISABLED", "8": "AVAILABLE"}, 
        "3": {"1": "DISABLED", "2": "AVAILABLE", "3": "DISABLED", "4": "AVAILABLE", "5": "DISABLED", "6": "AVAILABLE", "7": "DISABLED", "8": "AVAILABLE"}, 
        "4": {"1": "DISABLED", "2": "AVAILABLE", "3": "DISABLED", "4": "AVAILABLE", "5": "DISABLED", "6": "AVAILABLE", "7": "DISABLED", "8": "AVAILABLE"}
      }, 
      clean: {"1": "READY", "3": "READY", "4": "READY"}, edit: "READY", identify: "READY", 
      plan: "READY", plan_loop: "DISABLED", plan_run: "DISABLED", reference: "READY", run: "READY", standby: "ACTIVE"
    },
  };

  const modal_info = {
    initialized: false,
    modal_info: {
      "show": false,
      "html": "<h2 class='test'>Example Modal Dialog</h2><p>Test message</p>",
      "num_buttons": 2,
      "buttons": {
        "1": {
          "caption": "OK",
          "className": "btn btn-success btn-large",
          "response": "modal_ok"
        },
        "2": {
          "caption": "Cancel",
          "className": "btn btn-danger btn-large",
          "response": "modal_close"
        }
      }
    }
  };

  const plan = {
    initialized: true,
    plan: {
      "max_steps": 32,
      "panel_to_show": 0,
      "current_step": 1,
      "looping": false,
      "focus": {
        "row": 1,
        "column": 1
      },
      "last_step": 0,
      "steps": {},
      "num_plan_files": 0,
      "plan_files": {},
      "plan_filename": "",
      "bank_names": {
        "1": {
          "name": "Bank 1",
          "channels": {
            "1": "Ch. 1",
            "2": "Ch. 2",
            "3": "Ch. 3",
            "4": "Ch. 4",
            "5": "Ch. 5",
            "6": "Ch. 6",
            "7": "Ch. 7",
            "8": "Ch. 8"
          }
        },
        "2": {
          "name": "Bank 2",
          "channels": {
            "1": "Ch. 1",
            "2": "Ch. 2",
            "3": "Ch. 3",
            "4": "Ch. 4",
            "5": "Ch. 5",
            "6": "Ch. 6",
            "7": "Ch. 7",
            "8": "Ch. 8"
          }
        },
        "3": {
          "name": "Bank 3",
          "channels": {
            "1": "Ch. 1",
            "2": "Ch. 2",
            "3": "Ch. 3",
            "4": "Ch. 4",
            "5": "Ch. 5",
            "6": "Ch. 6",
            "7": "Ch. 7",
            "8": "Ch. 8"
          }
        },
        "4": {
          "name": "Bank 4",
          "channels": {
            "1": "Ch. 1",
            "2": "Ch. 2",
            "3": "Ch. 3",
            "4": "Ch. 4",
            "5": "Ch. 5",
            "6": "Ch. 6",
            "7": "Ch. 7",
            "8": "Ch. 8"
          }
        }
      },
      "available_ports": {
        "1": 170,
        "2": 0,
        "3": 170,
        "4": 170
      }
    }
  };

  const apiLoc = `${window.location.hostname}:8000/controller`;
  const socketURL = `ws://${apiLoc}/ws`;
  const mockWS = jest.fn((element) => {return element});
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);


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
          ...defaultState
        });
    });

    it('ComponentDidMount', async () => {
      const spy = jest.spyOn(Main.prototype, 'componentDidMount');
      const wrapper = mount(<Main />);
      expect(spy).toHaveBeenCalled();
      spy.mockReset();
      spy.mockRestore();
    })

    it('API test', async () => {
      const response = await (await PicarroAPI.getRequest(`http://${apiLoc}/uistatus`)).json()
      expect(response).toEqual(uistatus.uistatus);
      // const response1 = await (await PicarroAPI.getRequest(`http://${apiLoc}/ui`)).json()
    });

    it('handleData', () => {
      instance.handleData(JSON.stringify(uistatus));
      instance.handleData(JSON.stringify(plan));
      instance.handleData(JSON.stringify(modal_info));
      instance.handleData(JSON.stringify({}))
      instance.setState({initialized: false});
      instance.handleData(JSON.stringify({}))
    });

    it('WS', () => {
      instance.ws_sender(uistatus);
      expect(instance.ws.send).toBeTruthy();
    });

    it('setFocus', () => {
      instance.setFocus(1, 2);
      expect(instance.state.plan.focus).toEqual({row: 1, column: 2})
    });

    it('updateFileName', () => {
        instance.updateFileName.call(defaultState, true);
        expect(instance.state.isChanged).toEqual(true);
        instance.updateFileName.call(defaultState, false);
    });

    it('Modal', async () => {
      await server.connected;
      wrapper.setState({
        ...defaultState,
        modal_info: {
          show: true,
          html: "<div>Hello<div>"
        }
      });
      //expect a ws to be called on close
      const instance1 = wrapper.instance() as Main;
      instance1.ws_sender = mockWS;
      const modal = wrapper.find('Modal')
      const closeBtn = modal.find('CloseIcon').find('button');
      closeBtn.simulate('click');
      const element = mockWS.mock.calls[0][0];
      client.send(element);
      expect(instance1.ws_sender).toHaveBeenCalled();
      mockWS.mockClear();
      wrapper.setState({
        ...defaultState,
        modal_info: {
          "show": true,
          "html": "<h2 class='test'>Confirm file overwrite</h2><p>File exists. Overwrite?</p>",
          "num_buttons": 2,
          "buttons": {
            "1": {
              "caption": "OK",
              "className": "btn btn-success btn-large",
              "response": "modal_ok"
            },
            "2": {
              "caption": "Cancel",
              "className": "btn btn-danger btn-large",
              "response": "modal_close"
            }
          }
        }
      });
      const instance2 = wrapper.instance() as Main;
      instance2.ws_sender = mockWS;
      const modal2 = wrapper.find('Modal')
      const cancelBtn = modal2.find('button').at(1);
      cancelBtn.simulate('click');
      const element2 = mockWS.mock.calls[0][0];
      console.log(element2)
      client.send(element2);
      expect(instance2.ws_sender).toHaveBeenCalled();
      mockWS.mockClear();
      //test onclick will send a message to ws
      wrapper.setState({
        ...defaultState,
        modal_info: {
          show: false
        }
      });
    });

    it('Check banks render', () => {

    });

    it('Test Toast', () => {
      notifyError( <div>
        <h6>
          <b>Web Socket Disconnected!</b>
        </h6>
      </div>);
      const toast = wrapper.find('ToastContainer');
      expect(toast).toMatchSnapshot();
      notifySuccess( <div>
        <h6>
          <b>Web Socket Connected!</b>
        </h6>
      </div>);
      const toastSuccess = wrapper.find('ToastContainer');
      expect(toastSuccess).toMatchSnapshot();
    });
    server.close;
    client.close;
});
describe('<Main w/ PlanPanel />', () => {
  const wrapper = mount(<Main />);
  wrapper.setState({...defaultState1});

  it('Snapshot', () => {
      expect(wrapper).toMatchSnapshot();
  });

  it('Check reference button appears', async () => {
    const instance = wrapper.instance() as Main;
    instance.ws_sender = mockWS;
    

    await server.connected;

    const refBtn = wrapper.find('button#reference')
    refBtn.simulate('click');  
    console.log("HEllo", mockWS.mock.calls);
  
    const element = mockWS.mock.calls[0][0];
    console.log(element)
    client.send(element);
    expect(instance.ws_sender).toHaveBeenCalled();
    server.closed;
    mockWS.mockClear();
  });
});