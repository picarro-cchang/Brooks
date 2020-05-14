import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import "jest-fetch-mock";
import PlanLayout from "../../components/Plan/PlanLayout";
import { PlanLayoutProps, Plan } from "../../components/types";
import mockPlan from "../../api/__mocks__/mockPlan.json";
import mockData from "./../../api/__mocks__/mockData.json";
import LoadPanel from "../../components/Plan/LoadPanel";
import PlanPanel from "../../components/Plan/PlanPanel";

const mockWS = jest.fn();
const mockLayoutSwitch = jest.fn();
const mockGetPlanFileNames = jest.fn();
const defaultProps: PlanLayoutProps = {
  uistatus: mockData,
  plan: mockPlan,
  fileNames: ["Test, Test5"],
  layoutSwitch: mockLayoutSwitch,
  getPlanFileNames: mockGetPlanFileNames,
  loadedFileName: "Test5"
};

// jest.mock("./../api/PicarroAPI.ts");
jest.mock("./../../api/PlanService.ts")

describe("<PlanLayout />", () => {
  const addChanneToPlanRef = jest.spyOn(PlanLayout.prototype, "addChanneltoPlan");
  const updatePanelToShow = jest.spyOn(PlanLayout.prototype, "updatePanelToShow");
  const updateFileName = jest.spyOn(PlanLayout.prototype, "updateFileName");
  const setModal = jest.spyOn(PlanLayout.prototype, "setModalInfo");
  const deleteFile = jest.spyOn(PlanLayout.prototype, "deleteFile")
  const wrapper = shallow(<PlanLayout {...defaultProps} />);
  const mountwrapper = mount(<PlanLayout {...defaultProps} />)
  const instance = mountwrapper.instance() as PlanLayout;

  it("Match Snapshot", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders Correct Component", () => {
    wrapper.setState({ panel_to_show: 1 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("LoadPanel").html()).toBeDefined();
    wrapper.setState({ panel_to_show: 2 });
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("SavePanel").html()).toBeDefined();
  });

  it("getPlanFromFileName", async () => {
    const getPlan = jest.spyOn(instance, "getPlanFromFileName");
    mountwrapper.setState({panel_to_show: 1})
    mountwrapper.setProps({fileNames:[ "TestFile"]})
    const load = mountwrapper.find('LoadPanel').find('button#plan-filename-1')
    await load.simulate("click")
    expect(getPlan).toHaveBeenCalled()
  });

  it("planSaved", async () => {
    const planSaved = jest.spyOn(instance, "planSaved");
    // const setModal = jest.spyOn(instance, "setModalInfo");
    mountwrapper.setState({panel_to_show: 2})
    const input = mountwrapper.find('SavePanel').find('input#fileName')
    input.simulate('change', { target: { value: 'Plan2' } });
    const load = mountwrapper.find('SavePanel').find('button#save-btn');
    load.simulate("click");
    expect(mountwrapper).toMatchSnapshot();
    expect(setModal).toHaveBeenCalled();
    const modalOK = mountwrapper.find('Modal').find('button#save')
    modalOK.simulate("click");
    expect(planSaved).toHaveBeenCalled();
    expect(setModal).toHaveBeenCalled();
  });

  it("planOverwrite", ()=> {
    const planOverwrite = jest.spyOn(instance, "planOverwrite");
    mountwrapper.setState({panel_to_show: 0})
    mountwrapper.setState({isEdited: true})
    const input = mountwrapper.find('PlanPanel').find('button#ok-btn')
    input.simulate("click");
    expect(mountwrapper).toMatchSnapshot();
    expect(setModal).toHaveBeenCalled();
    const modalOK = mountwrapper.find('Modal').find('button').at(0)
    modalOK.simulate("click");
    expect(planOverwrite).toHaveBeenCalled();
  })

  it("addChannelToPlan", () => {
    mountwrapper.setState({isPlanPanel: true})
    const reference = mountwrapper.find('button#reference');
    reference.simulate("click");
    expect(addChanneToPlanRef).toHaveBeenCalled();
  });

  it("updatePanelToShow", () => {
    mountwrapper.setState({panel_to_show: 0})
    const button = mountwrapper.find('PlanPanel').find('button').at(2);
    button.simulate('click');
    expect(updatePanelToShow).toHaveBeenCalled();
  });

  it("updateFileName", () => {
    mountwrapper.setState({panel_to_show: 0})
    const button = mountwrapper.find('PlanPanel').find('input#plan-port-1');
    button.simulate('change');
    expect(updateFileName).toHaveBeenCalled();
  });

  it("deleteFile", () => {
    mountwrapper.setState({panel_to_show: 1})
    const file = mountwrapper.find('LoadPanel').find('button').at(1)
    file.simulate('click')
    expect(deleteFile).toHaveBeenCalled()
  })

});
