import React from 'react';
import { shallow, mount } from 'enzyme';
import 'jest-styled-components';
import WS from "jest-websocket-mock";
import { EditPanelOptions } from '../../types';
import EditForm from '../EditForm';

const mockClick = jest.fn((element) => {return element;});

const defaultProps: EditPanelOptions = {
    uistatus: {
        "bank": {
            "1" : "READY",
            "2" : "READY",
            "3" : "DISABLED"
        }
    },
    ws_sender: mockClick,
    plan: {
        "max_steps": 32,
        "panel_to_show": 0,
        "current_step": 8,
        "focus": {
            "row": 15,
            "column": 1
        },
        "last_step": 14,
        "steps": {
            "1": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 1
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "2": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 2
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "3": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 4
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "4": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 8
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "5": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 16
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "6": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 32
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "7": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 64
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "8": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 128
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "9": {
            "banks": {
                "1": {
                "clean": 1,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 0,
            "duration": 30
            },
            "10": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 0
                }
            },
            "reference": 1,
            "duration": 30
            },
            "11": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 1
                }
            },
            "reference": 0,
            "duration": 30
            },
            "12": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 2
                }
            },
            "reference": 0,
            "duration": 30
            },
            "13": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 4
                }
            },
            "reference": 0,
            "duration": 30
            },
            "14": {
            "banks": {
                "1": {
                "clean": 0,
                "chan_mask": 0
                },
                "2": {
                "clean": 0,
                "chan_mask": 8
                }
            },
            "reference": 0,
            "duration": 30
            }
        },
        "num_plan_files": 7,
        "plan_files": {
            "1": "1234567890123456789012345678",
            "2": "30_seconds",
            "3": "__default__",
            "4": "abcdefghijklmnopqrstwxyzabc",
            "5": "abcdefghijklmnopqrstwxyzabcd",
            "6": "kp_test",
            "7": "kp_test_2"
        },
        "plan_filename": "__default__",
        "bank_names": {
            "1": {
            "name": "B 1",
            "channels": {
                "1": "Channel 1",
                "2": "Channel 2",
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
        },
    }
};


describe('<EditForm />', () => {
  const part = mount(<EditForm {...defaultProps} />);
  const wrapper = shallow(<EditForm {...defaultProps} />);

  it('Renders correctly', () => {
    expect(wrapper).toMatchSnapshot();
  });

  it('Renders with correct bank/channel Names', () => {
      const value = wrapper.find('input[name="bank1"]').props().value;
      const chn2value = wrapper.find('input[name="bank12"]').props().value;

      expect(value).toEqual('B 1');
      expect(chn2value).toEqual('Channel 2');

  });

});

