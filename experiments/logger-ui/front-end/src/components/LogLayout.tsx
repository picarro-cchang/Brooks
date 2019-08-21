import React, { Component, Fragment } from 'react';
import { Cell } from './Cell/Cell';
import { LogSectionProps } from './types';

interface Props extends LogSectionProps { }


export class LogLayout extends Component<Props, any> {
  constructor(props: any) {
    super(props);
  }

  render() {
    const { data } = this.props.options;
    return (
      <Fragment>
        <div className="container-fluid">
          {data.map((cell: string[]) => (
            <Cell key={Math.random()} row={cell} />
          ))}
        </div>
      </Fragment>
    );
  }
}
