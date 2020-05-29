import React from 'react';
import CustomSelect, {Props} from './../components/CustomSelect';
import { shallow } from 'enzyme';

const defaultProps: Props = {
    passedOptions: [],
    passedOnChange: (x: any) => null,
    allOption: {
        value: 'All',
        label: 'All'
    },
    value: []
}
describe('<DataGeneratorPanel/>', () => {
  const wrapper = shallow(<CustomSelect {...defaultProps}  />);

  it('Create Snapshot', () => {
    expect(wrapper).toMatchSnapshot();
  });
});
