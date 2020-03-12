import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import WS from "jest-websocket-mock";
import Modal from "react-responsive-modal";
import PlanPanel from "../components/PlanPanel";
import { PlanPanelOptions, Plan } from "../types";
import mockPlanPanelData from "./../api/__mocks__/mockPlanPanel.json";
import mockBankNames from "./../api/__mocks__/mockBankNames.json";
import validate from "./../api/__mocks__/mockValidation";

const mockSetFocus = jest.fn();
const mockUpdateFilename = jest.fn();
const mockWSSender = jest.fn(element => {
  // if plan, validate, else
  return element;
});
const mockAddChanneltoPlan = jest.fn();

const apiLoc = `${window.location.hostname}:8000/controller`;
const socketURL = `ws://${apiLoc}/ws`;

const defaultProps: PlanPanelOptions = {
  uistatus: {},
  plan: mockPlanPanelData,
  setFocus: mockSetFocus,
  ws_sender: mockWSSender,
  isChanged: false,
  updateFileName: mockUpdateFilename,
  addChanneltoPlan: mockAddChanneltoPlan
};

describe("<PlanPanel />", () => {
  const wrapper = shallow(<PlanPanel {...defaultProps} />);
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

  it("onFocus for Plan Channel", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-port-1");
    elem.simulate("focus");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_panel",
      focus: { column: 1, row: 1 }
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_panel", focus: { column: 1, row: 1 } }
    ]);
    mockWSSender.mockClear();
    server.close;
  });

  it("onChange for Plan Channel", () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-port-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
  });

  it("onFocus for Plan Duration", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-duration-1");
    elem.simulate("focus");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_panel",
      focus: { column: 2, row: 1 }
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_panel", focus: { column: 2, row: 1 } }
    ]);
    mockWSSender.mockClear();
    server.close;
  });

  it("onChange for Plan Duration", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-duration-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_panel",
      row: 1,
      duration: "20"
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_panel", row: 1, duration: "20" }
    ]);
    mockWSSender.mockClear();
    server.close;
  });

  it("onChange for Plan Radio", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const planList = shallow.find("ReactList");
    const elem = planList.find("input#plan-row-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({
      element: "plan_panel",
      current_step: 1
    });
    expect(server).toHaveReceivedMessages([
      { element: "plan_panel", current_step: 1 }
    ]);
    mockWSSender.mockClear();
    server.close;
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
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const insertButton = shallow.find("span#cancel-x");
    insertButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_cancel" });
    expect(server).toHaveReceivedMessages([{ element: "plan_cancel" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Insert Button", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const insertButton = shallow.find("button#insert-btn");
    insertButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_insert" });
    expect(server).toHaveReceivedMessages([{ element: "plan_insert" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Save Button", async () => {
    // need validation
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const validation = validate(shallow.props().plan);
    expect(validation).toBe(true);
    const saveButton = shallow.find("button#save-btn");
    saveButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_save" });
    expect(server).toHaveReceivedMessages([{ element: "plan_save" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Load Button", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const loadButton = shallow.find("button#load-btn");
    loadButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_load" });
    expect(server).toHaveReceivedMessages([{ element: "plan_load" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Delete Button", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const deleteButton = shallow.find("button#delete-btn");
    deleteButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    expect(mockUpdateFilename).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_delete" });
    expect(server).toHaveReceivedMessages([{ element: "plan_delete" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Clear Button", async () => {
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const clearButton = shallow.find("button#clear-btn");
    clearButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    expect(mockUpdateFilename).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_clear" });
    expect(server).toHaveReceivedMessages([{ element: "plan_clear" }]);
    mockWSSender.mockClear();
    server.close;
  });

  it("Ok Button", async () => {
    // needs validation
    mockWSSender.mockClear();
    await server.connected;
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const validation = validate(shallow.props().plan);
    expect(validation).toBe(true);
    const okButton = shallow.find("button#ok-btn");
    okButton.simulate("click");
    const element = mockWSSender.mock.calls[0][0];
    client.send(element);
    expect(mockWSSender).toHaveBeenCalled();
    expect(mockUpdateFilename).toHaveBeenCalled();
    await expect(server).toReceiveMessage({ element: "plan_ok" });
    expect(server).toHaveReceivedMessages([{ element: "plan_ok" }]);
    mockWSSender.mockClear();
    server.close;
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
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
    updateFileName: mockUpdateFilename
  };
  expect(validate(props.plan)).toEqual(
    Error("Invalid channel selection for bank")
  );
});
