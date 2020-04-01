import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import Modal from "react-responsive-modal";
import PlanPanel from "./../../components/Plan/PlanPanel";
import { PlanPanelOptions, Plan } from "./../../components/types";
import mockPlanPanelData from "./../../api/__mocks__/mockPlanPanel.json";
import mockBankNames from "./../../api/__mocks__/mockBankNames.json";
import validate from "./../../api/__mocks__/mockValidation";

const mockSetFocus = jest.fn();
const mockUpdateFilename = jest.fn();
const mockWSSender = jest.fn(element => {
  // if plan, validate, else
  return element;
});
const mockUpdatePanel = jest.fn();
const mockLayoutSwitch = jest.fn();
const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: PlanPanelOptions = {
  uistatus: {},
  plan: mockPlanPanelData,
  setFocus: mockSetFocus,
  ws_sender: mockWSSender,
  isChanged: false,
  updateFileName: mockUpdateFilename,
  bankAddition: {},
  updatePanel: mockUpdatePanel, 
  fileName: "",
  layoutSwitch: mockLayoutSwitch
};

describe("<PlanPanel />", () => {
  const wrapper = shallow(<PlanPanel {...defaultProps} />);
  const shallowwrapper = mount(<PlanPanel {...defaultProps} />);
  const instance = wrapper.instance() as PlanPanel;
  const server = new WS(socketURL);
  const client = new WebSocket(socketURL);
  instance.manageFocus = jest.fn();

  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("makePlanRow", () => {
    const value = instance.makePlanRow(5);
    expect(value).toMatchSnapshot();
  });

  it("shouldComponentUpdate", () => {
  });

  it("onFocus for Plan Channel", async () => {
  });

  it("onChange for Plan Channel", () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-port-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
  });

  it("onFocus for Plan Duration", async () => {
  });

  it("onChange for Plan Duration", async () => {
    // const shallow = mount(<PlanPanel {...defaultProps} />);
    // const planList = shallow.find("ReactList");
    // const elem = planList.find("input#plan-duration-1");
    // elem.simulate("change");
    // expect(mockUpdateFilename).toHaveBeenCalled();
    // //expect updateduration to have been called
  });

  it("onChange for Plan Radio", async () => {
    //expect updatecurrentsetp to be called
  });

  it("renderItem", () => {
    instance.makePlanRow = jest.fn();
    const listItem = instance.renderItem(1, 1);
    expect(instance.makePlanRow).toHaveBeenCalled();
    expect(listItem).toMatchSnapshot();
  });

  it("ReactList renders", () => {
    const planList = mount(<PlanPanel {...defaultProps} />);
    expect(planList).toMatchSnapshot();
  });

  it("Cancel X", async () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const insertButton = shallow.find("span#cancel-x");
    insertButton.simulate("click");
    expect(mockLayoutSwitch).toHaveBeenCalled(); 
  });

  it("Insert Button", async () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const insertButton = shallow.find("button#insert-btn");
    insertButton.simulate("click");
    //expect insertrwo to be called
  });

  it("Save Button", async () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const validation = validate(shallow.props().plan);
    expect(validation).toBe(true);
    const saveButton = shallow.find("button#save-btn");
    saveButton.simulate("click");
   //expect savefile to be called
  });

  it("Load Button", async () => {
    const loadButton = shallowwrapper.find("button#load-btn");
    loadButton.simulate("click");
    expect(mockUpdatePanel).toHaveBeenCalled();
  });

  it("Delete Button", async () => {
    const deleteButton = shallowwrapper.find("button#delete-btn");
    deleteButton.simulate("click");
    expect(mockUpdateFilename).toHaveBeenCalled();
    //expect delete row to be called
  });

  it("Clear Button", async () => {
    const clearButton = shallowwrapper.find("button#clear-btn");
    clearButton.simulate("click");
    expect(mockUpdateFilename).toHaveBeenCalled();
    //clearplan
  });

  it("SaveAs Button", async () => {
    // needs validation
    const validation = validate(shallowwrapper.props().plan);
    expect(validation).toBe(true);
    const okButton = shallowwrapper.find("button#ok-btn");
    okButton.simulate("click");
    //expect saveas
  });

  it("ReactList renders", () => {
    const planList = mount(<PlanPanel {...defaultProps} />);
    planList.setProps({
      isChanged: true
    });
    expect(planList).toMatchSnapshot();
  });
});

describe("<PlanPanel /> For Clean not equal to 0", () => {
  const defaultPropsClean: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 1,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        1: {
          banks: {
            1: {
              clean: 10,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 1
        }
      },
      num_plan_files: 1,
      plan_filename: "test.pln",
      plan_files: {
        "1": "test.pln"
      },
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  const wrapper = shallow(<PlanPanel {...defaultPropsClean} />);
  const instance = wrapper.instance() as PlanPanel;

  it("ReactList renders", () => {
    const planList = mount(<PlanPanel {...defaultPropsClean} />);
    expect(planList).toMatchSnapshot();
  });
});

describe("<PlanPanel /> All Chan Masks == 0", () => {
  const defaultPropsRefFail: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 1,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 0
            },
            "2": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 20
        }
      },
      num_plan_files: 1,
      plan_filename: "test.pln",
      plan_files: {
        "1": "test.pln"
      },
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };

  const wrapper = shallow(<PlanPanel {...defaultPropsRefFail} />);

  it("ReactList renders", () => {
    const planList = mount(<PlanPanel {...defaultPropsRefFail} />);
    expect(planList).toMatchSnapshot();
  });
});

describe("<PlanPanel /> Rows greater than 10", () => {
  const defaultPropsRefFail: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 1,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 10
            },
            "2": {
              clean: 0,
              chan_mask: 10
            }
          },
          reference: 0,
          duration: 0
        }
      },
      num_plan_files: 1,
      plan_filename: "test.pln",
      plan_files: {
        "1": "test.pln"
      },
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };

  it("", () => {
    const test = new PlanPanel(defaultProps);
    const result = test.makePlanRow(10);
    expect(result).toMatchSnapshot();
  });

  it("ReactList renders", () => {
    const planList = mount(<PlanPanel {...defaultPropsRefFail} />);
    expect(planList).toMatchSnapshot();
  });
});

describe("<PlanPanel /> Validation Testing", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 2,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 2,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 2
            },
            "3": {
              clean: 0,
              chan_mask: 0
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 20
        },
        "2": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 32
            },
            "3": {
              clean: 0,
              chan_mask: 0
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 20
        }
      },
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  const wrapper = mount(<PlanPanel {...props} />);
});

it("Empty Plan", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 2,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  expect(validate(props.plan)).toEqual(Error("Plan is empty"));
});

it("Invalid Pending Step", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 3,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 2,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 2
            },
            "3": {
              clean: 0,
              chan_mask: 0
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 20
        }
      },
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  expect(validate(props.plan)).toEqual(
    Error("Pending Step must be in between 1 and " + props.plan.last_step)
  );
});

it("Invalid Duration", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 0
            },
            "3": {
              clean: 0,
              chan_mask: 0
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 1,
          duration: 10
        },
        "2": {
          banks: {
            "1": {
              clean: 10,
              chan_mask: 0
            },
            "3": {
              clean: 10,
              chan_mask: 0
            },
            "4": {
              clean: 10,
              chan_mask: 0
            }
          },
          reference: 0,
          duration: 20
        }
      },
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  expect(validate(props.plan)).toEqual(
    Error("Duration must be greater than 20")
  );
});

it("Invalid Bank", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 0
            },
            "2": {
              clean: 0,
              chan_mask: 0
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 1,
          duration: 30
        }
      },
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  expect(validate(props.plan)).toEqual(Error("Invalid Bank"));
});

it("Invalid Bank", () => {
  const props: PlanPanelOptions = {
    uistatus: {},
    plan: {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 1,
      focus: {
        row: 1,
        column: 2
      },
      last_step: 1,
      steps: {
        "1": {
          banks: {
            "1": {
              clean: 0,
              chan_mask: 0
            },
            "3": {
              clean: 0,
              chan_mask: 400
            },
            "4": {
              clean: 0,
              chan_mask: 0
            }
          },
          reference: 1,
          duration: 30
        }
      },
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: mockBankNames
    },
    setFocus: mockSetFocus,
    ws_sender: mockWSSender,
    isChanged: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch
  };
  expect(validate(props.plan)).toEqual(
    Error("Invalid channel selection for bank")
  );
});
