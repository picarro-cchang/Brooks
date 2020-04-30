import React, { Component, PureComponent, ReactText } from "react";
import { EditPanelOptions } from "../types";

class EditForm extends Component<any, any> {
  state = {
    plan: {
      bank_names: this.props.plan.bank_names
    }
  };
  banks: any;
  bank_list: any;

  render() {
    const edit_list = [];
    this.bank_list = [];
    this.banks = this.props.uistatus.bank;
    for (const num in this.banks) {
      const value = this.banks[num];
      if (value === "READY") {
        this.bank_list.push(num);
        edit_list.push(<div key={"bank" + num} className="row">
            <label className="edit-label"> Bank {num}</label>
      </div>)
        for (let i = 1; i <= 8; i++) {
          let portNumber = (Number(num) - 1) * 8 + i
          edit_list.push(
            <div key={portNumber} className="row">
              <label className="edit-label"> Port {portNumber}: </label>
              <input                
                name={"bank" + num + i}
                className="col-sm-6 edit-input"
                type="text"
                onChange={event =>
                  this.props.handleChannelNameChange(
                    event.target.value,
                    num.toString(),
                    i
                  )
                }
                value={this.props.plan.bank_names[num].channels[i]}
                maxLength={15}
              />
            </div>
          );
        }
      }
    }
    return (
      <div className="panel-plan-inner">
        <div className="gf-form-group">
          {edit_list}
        </div>
      </div>);
  }
}

export default EditForm;
