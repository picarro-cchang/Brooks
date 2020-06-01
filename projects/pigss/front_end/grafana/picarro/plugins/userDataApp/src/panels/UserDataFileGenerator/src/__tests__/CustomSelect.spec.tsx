import React from 'react';
import CustomSelect, { Props } from './../components/CustomSelect';
import { shallow, mount } from 'enzyme';

const defaultProps: Props = {
  passedOptions: [
    { value: 'H2O', label: 'H2O' },
    { value: 'CO2', label: 'CO2' },
  ],
  passedOnChange: (x: any) => null,
  allOption: {
    value: 'All',
    label: 'All',
  },
  value: ['H2O'],
};

describe('<DataGeneratorPanel/>', () => {
  const wrapper = shallow(<CustomSelect {...defaultProps} />);
  const mt = mount(<CustomSelect {...defaultProps} />);
  //   const instance = wrapper.instance() as CustomSelect;
  it('Create Snapshot', () => {
    expect(wrapper).toMatchSnapshot();
  });

  it('Option snapshot', () => {
    const input = mt.find('input');
    const control = mt.find('div.list__control');
    input.simulate('focus');
    control.simulate('mouseDown');
    expect(
      mt
        .find('.list__option')
        .at(0)
        .text()
    ).toBe('   H2O');
    mt.find('.list__option')
      .at(0)
      .simulate('click');
    expect(mt.find('.list__multi-value').text()).toBe('H2O');
  });
});
