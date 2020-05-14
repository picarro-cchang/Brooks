import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import "jest-fetch-mock"
import WS from "jest-websocket-mock";
import Modal from "react-responsive-modal";
import PlanPanel from "./../../components/Plan/PlanPanel";
import { PlanPanelOptions, Plan } from "./../../components/types";
import mockPlanPanelData from "./../../api/__mocks__/mockPlanPanel.json";
import mockBankNames from "./../../api/__mocks__/mockBankNames.json";
import validate from "./../../api/__mocks__/mockValidation";
import mockData from "./../../api/__mocks__/mockData.json"

const mockUpdateFilename = jest.fn();
const mockWSSender = jest.fn(element => {
  return element;
});
const mockUpdatePanel = jest.fn();
const mockLayoutSwitch = jest.fn();
const mockPlanSavedAs = jest.fn();
const mockPlanOverwrite =  jest.fn();
const mockGetStateFromSavedData = jest.fn();
const mockSetPlanStorage = jest.fn();
const mockSetModalInfo = jest.fn();
const mockUpdateSavedFileState = jest.fn();

const defaultProps: PlanPanelOptions = {
  planID: "",
  uistatus: mockData,
  plan: mockPlanPanelData,
  isEdited: false,
  updateFileName: mockUpdateFilename,
  bankAddition: {bank: 1, channel: 1},
  updatePanel: mockUpdatePanel, 
  fileName: "TestPlan",
  layoutSwitch: mockLayoutSwitch,
  planOverwrite: mockPlanOverwrite,
  setModalInfo: mockSetModalInfo,
  updateSavedFileState: mockUpdateSavedFileState
};

const nextProps: PlanPanelOptions = {
  planID: "",
  uistatus: mockData,
  plan: mockPlanPanelData,
  isEdited: false,
  updateFileName: mockUpdateFilename,
  bankAddition: {bank: 1, channel: 6},
  updatePanel: mockUpdatePanel, 
  fileName: "TestPlan",
  layoutSwitch: mockLayoutSwitch,
  planOverwrite: mockPlanOverwrite,
  setModalInfo: mockSetModalInfo,
  updateSavedFileState: mockUpdateSavedFileState
};

const defaultState = {
  bankAdditionClicked: {},
  isLoaded: false,
  refVisible: true,
  isChanged: defaultProps.isEdited,
  plan: mockPlanPanelData,
  fileName: defaultProps.fileName
};
describe("<PlanPanel />", () => {
  const overwriteFile = jest.spyOn(PlanPanel.prototype, "overwriteFile")
  const wrapper = shallow(<PlanPanel {...defaultProps} />);
  wrapper.setState({defaultState})
  const shallowwrapper = mount(<PlanPanel {...defaultProps} />);
  const instance = wrapper.instance() as PlanPanel;
  const instance2 = shallowwrapper.instance() as PlanPanel;
  instance.manageFocus = jest.fn();


  it("Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("makePlanRow", () => {
    const value = instance.makePlanRow(5);
    expect(value).toMatchSnapshot();
  });

  it("shouldComponentUpdate", () => {
    const changeChannels = jest.spyOn(instance2, "changeChannelstoProperFormat")
    const addToPlan = jest.spyOn(instance2, "addToPlan")
    instance2.shouldComponentUpdate(nextProps);
    expect(changeChannels).toHaveBeenCalled();
    expect(addToPlan).toHaveBeenCalled();
  });

  it("onFocus for Plan Channel", () => {
    const onFocus = jest.spyOn(shallowwrapper.instance() as PlanPanel, "updateFocus")
    const channelFocus = shallowwrapper.find("input#plan-port-1");
    channelFocus.simulate("focus");
    expect(onFocus).toHaveBeenCalled();
  });

  it("onChange for Plan Channel", () => {
    const planList = shallowwrapper.find("ReactList");
    const elem = planList.find("input#plan-port-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
  });

  it("onFocus for Plan Duration", () => {
    const onFocus = jest.spyOn(shallowwrapper.instance() as PlanPanel, "updateFocus")
    const channelFocus = shallowwrapper.find("input#plan-duration-1");
    channelFocus.simulate("focus");
    expect(onFocus).toHaveBeenCalled();
  });

  it("onChange for Plan Duration", () => {
    const updateDuration = jest.spyOn(shallowwrapper.instance() as PlanPanel, "updateDuration")
    const planList = shallowwrapper.find("ReactList");
    const elem = planList.find("input#plan-duration-1");
    elem.simulate("change");
    expect(mockUpdateFilename).toHaveBeenCalled();
    expect(updateDuration).toHaveBeenCalled();
  });

  it("onChange for Plan Radio", () => {
    const updateCurrentStep = jest.spyOn(shallowwrapper.instance() as PlanPanel, "updateCurrentStep")
    const planList = shallowwrapper.find("ReactList");
    const elem = planList.find("input#plan-row-1");
    elem.simulate("change");
    expect(updateCurrentStep).toHaveBeenCalled();
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

  it("Cancel X", () => {
    const shallow = mount(<PlanPanel {...defaultProps} />);
    const insertButton = shallow.find("span#cancel-x");
    insertButton.simulate("click");
    expect(mockLayoutSwitch).toHaveBeenCalled(); 
  });

  it("SaveAs Button", () => {
    const validation = validate(shallowwrapper.props().plan);
    expect(validation).toBe(true);
    shallowwrapper.setProps({isEdited: true})
    const saveAsButton = shallowwrapper.find("button#ok-btn");
    saveAsButton.simulate("click");
    expect(overwriteFile).toHaveBeenCalled();
    expect(mockSetModalInfo).toHaveBeenCalled();
  });

  it("Save Button", () => {
    const spy = jest.spyOn(PlanPanel.prototype, 'saveFile')
    const validation = validate(shallowwrapper.props().plan);
    expect(validation).toBe(true);
    const saveButton = shallowwrapper.find("button#save-btn");
    saveButton.simulate("click");
    expect(spy).toHaveBeenCalled();
  });
  
  

  it("Load Button", () => {
    const loadButton = shallowwrapper.find("button#load-btn");
    loadButton.simulate("click");
    expect(mockUpdatePanel).toHaveBeenCalled();
  });

  it("Delete Button", () => {
    const deleteRow = jest.spyOn(shallowwrapper.instance() as PlanPanel, "deleteRow")
    const deleteButton = shallowwrapper.find("button#delete-btn");
    deleteButton.simulate("click");
    expect(mockUpdateFilename).toHaveBeenCalled();
    expect(deleteRow).toHaveBeenCalled();
  });

 it("Insert Button", () => {
    const insertRow = jest.spyOn(shallowwrapper.instance() as PlanPanel, 'insertRow')
    const insertButton = shallowwrapper.find("button#insert-btn");
    insertButton.simulate("click");
    expect(insertRow).toHaveBeenCalled();
  });
  
  it("Clear Button", () => {
    const clearPlan = jest.spyOn(shallowwrapper.instance() as PlanPanel, "clearPlan")
    const setModal = jest.spyOn(shallowwrapper.instance() as PlanPanel, "setModalInfo")
    const clearButton = shallowwrapper.find("button#clear-btn");
    clearButton.simulate("click");
    expect(setModal).toHaveBeenCalled();
    const modal = shallowwrapper.find('Modal').find('button').at(0)
    modal.simulate('click')
    expect(mockUpdateFilename).toHaveBeenCalled();
    expect(clearPlan).toHaveBeenCalled();
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
    planID: "",
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
    isEdited: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch,
    planOverwrite: mockPlanOverwrite,
    setModalInfo: mockSetModalInfo,
    updateSavedFileState: mockUpdateSavedFileState
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
    planID: "",
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
    isEdited: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch,
    planOverwrite: mockPlanOverwrite,
  setModalInfo: mockSetModalInfo,
  updateSavedFileState: mockUpdateSavedFileState
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
    planID: "",
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
    isEdited: false,
    updateFileName: mockUpdateFilename,
    bankAddition: {},
    updatePanel: mockUpdatePanel, 
    fileName: "",
    layoutSwitch: mockLayoutSwitch,
    planOverwrite: mockPlanOverwrite,
  setModalInfo: mockSetModalInfo,
  updateSavedFileState: mockUpdateSavedFileState
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
