import React, { Component } from 'react';
import { CellProps } from '../types';
import './Cells.css';
interface Props extends CellProps {}
export class Cell extends Component<Props> {
  constructor(props: Props) {
    super(props);
  }
  render() {
    const { row } = this.props;
    return (
      <div className="row log-row">
        {/* Timestamp */}
        <div className="log-fields timestamp">{row[1]}</div>
        {/* Client Name */}
        <div className="log-fields client-name">{row[2]}</div>
        {/* Severity Level */}
        <div className={'log-fields ' + 'severity-level-' + row[4]}>{row[4]}</div>
        {/* Epoch Time */}
        {/* <div className="log-fields">{row[2]}</div> */}
        {/* Log Message */}
        <div className="log-fields log-message">{row[3]}</div>
      </div>
    );
  }
}
