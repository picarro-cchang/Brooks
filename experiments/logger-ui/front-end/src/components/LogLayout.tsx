import React, { Component, Fragment } from 'react';
import { Cell } from './Cell/Cell';
import { LogSectionProps } from './types';

interface Props extends LogSectionProps {}

export class LogLayout extends Component<Props, any> {
  constructor(props: any) {
    super(props);
  }

  render() {
    const { data } = this.props.options;
    const styleObj = {
      overflow: "scroll",
      height: "inherit"
    };

    return (
      <Fragment>
        <h3 className="text-center" style={{"marginTop":"24px"}}>Logs</h3>
        <div className="container-fluid" style={styleObj}>
          {data.map((cell: string[]) => (
            <Cell key={Math.random()} row={cell} />
          ))}
        </div>
      </Fragment>
    );
  }
}
