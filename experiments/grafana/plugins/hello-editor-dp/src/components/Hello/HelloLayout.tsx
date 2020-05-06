import React, { Component } from 'react';

import { HelloProps } from '../../types';
interface Props extends HelloProps {}

export class HelloLayout extends Component<Props, any> {
  constructor(props: any) {
    super(props);
    this.state = { name: '' };
  }

  render() {
    const { options } = this.props;
    const { name } = options;
    return (
      <div className="gf-form">
        <span className="gf-form-label width-4">Hello</span>
        <input type="text" className="gf-form-input width-8" value={name} />
      </div>
    );
  }
}
