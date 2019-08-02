import React, { Component } from 'react';

import { HelloProps } from '../../types';
interface Props extends HelloProps { }

export class HelloLayout extends Component<Props, any> {
    constructor(props) {
        super(props);
        this.state = { worldString: '' };
    }

    render() {
        const { options } = this.props;
        const { worldString } = options;
        return (
          <div className="gf-form">
              <span className="gf-form-label width-4">Hello</span>
              <input
                type="text"
                className="gf-form-input width-8"
                value={worldString}
              />
          </div>
        );
    }
}
