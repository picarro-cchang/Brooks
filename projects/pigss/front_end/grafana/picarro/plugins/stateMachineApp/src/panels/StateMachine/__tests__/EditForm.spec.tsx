import React from "react";
import { shallow, mount } from "enzyme";
import "jest-styled-components";
import EditForm from "../components/EditForm";
import mockPlan from "./../api/__mocks__/mockPlan.json";

const mockClick = jest.fn(element => {
  return element;
});
const mockHandleBankChange = jest.fn();
const mockHandleChannelNameChange = jest.fn();

const defaultProps = {
  uistatus: {
    bank: {
      "1": "READY",
      "2": "READY",
      "3": "DISABLED"
    }
  },
  ws_sender: mockClick,
  plan: mockPlan,
  handleBankChange: mockHandleBankChange,
  handleChannelNameChange: mockHandleChannelNameChange
};

describe("<EditForm />", () => {
  const part = mount(<EditForm {...defaultProps} />);
  const wrapper = shallow(<EditForm {...defaultProps} />);
  const event = {
    target: {
      name: "bank num",
      value: "Bank Number Name"
    }
  };
  const event2 = {
    target: {
      name: "channel num",
      value: "Channel Number Name"
    }
  };

  it("Renders correctly", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("Renders with correct bank/channel Names", () => {
    const value = wrapper.find('input[name="bank1"]').props().value;
    const chn2value = wrapper.find('input[name="bank12"]').props().value;

    expect(value).toEqual("Bank 1");
    expect(chn2value).toEqual("Ch. 2");
  });

  it("onChange event for Bank", () => {
    wrapper.find('input[name="bank1"]').simulate("change", event);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleBankChange.mock.calls[0]).toEqual([
      "Bank Number Name",
      "1"
    ]);
  });

  it("onChange event for Channel 1", () => {
    wrapper.find('input[name="bank11"]').simulate("change", event2);
    expect(mockHandleChannelNameChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      1
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 2", () => {
    wrapper.find('input[name="bank12"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      2
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 3", () => {
    wrapper.find('input[name="bank13"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      3
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 4", () => {
    wrapper.find('input[name="bank14"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      4
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 5", () => {
    wrapper.find('input[name="bank15"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      5
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 6", () => {
    wrapper.find('input[name="bank16"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      6
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 7", () => {
    wrapper.find('input[name="bank17"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      7
    ]);
    mockHandleChannelNameChange.mockClear();
  });
  it("onChange event for Channel 8", () => {
    wrapper.find('input[name="bank18"]').simulate("change", event2);
    expect(mockHandleBankChange).toHaveBeenCalled();
    expect(mockHandleChannelNameChange.mock.calls[0]).toEqual([
      "Channel Number Name",
      "1",
      8
    ]);
    mockHandleChannelNameChange.mockClear();
  });
});
