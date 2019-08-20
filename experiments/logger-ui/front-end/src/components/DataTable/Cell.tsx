import React, { Component } from 'react';
import { CellType } from './types';
import './Cells.css';
interface Props extends CellType {}
export class Cell extends Component<Props> {
  constructor(props: Props) {
    super(props);
  }
  render() {
    const { data } = this.props;
    return (
      <div className="row log-row">
        {/* Timestamp */}
        <div className="log-fields timestamp">{data[0]}</div>
        {/* Client Name */}
        <div className="log-fields client-name">{data[1]}</div>
        {/* Severity Level */}
        <div className={"log-fields " + "severity-level-"+data[3]}>{data[3]}</div>
        {/* Log Message */}
        <div className="log-fields log-message">{data[2]}</div>
      </div>
    );
  }
}
