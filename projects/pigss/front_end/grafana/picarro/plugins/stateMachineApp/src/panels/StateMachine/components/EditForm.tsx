import React, { Component, PureComponent, ReactText } from "react";
import { EditPanelOptions } from "../types";

export class EditForm extends Component<any, any> {

  banks: any;
  bank_list: any;

  render() {
    let edit_list = [];
    this.bank_list = [];
    this.banks = this.props.uistatus.bank;
    for (let num in this.banks) {
      let value = this.banks[num];
      if (value === "READY") {
        this.bank_list.push(num);
        edit_list.push(
          <div className="gf-form-group">
            <div className="row">
              <label className="edit-label"> Bank {num}</label>
              <input
                name={"bank" + num}
                className="col-sm-6 edit-input"
                type="text"
                value={this.props.plan.bank_names[num].name}
                onChange={(event) => this.props.handleBankChange(event.target.value,  num.toString())}
                maxLength={14}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 1 </label>
              <input
                name={"bank" + num + "1"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 1)}
                value={this.props.plan.bank_names[num].channels[1]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 2 </label>
              <input
                name={"bank" + num + "2"}
                className="col-sm-6 edit-input"
                type="text"
                value={this.props.plan.bank_names[num].channels[2]}
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 2)}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 3 </label>
              <input
                name={"bank" + num + "3"}
                className="col-sm-6 edit-input"
                type="text"
                value={this.props.plan.bank_names[num].channels[3]}
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 3)}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 4 </label>
              <input
                name={"bank" + num + "4"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 4)}
                value={this.props.plan.bank_names[num].channels[4]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 5 </label>
              <input
                name={"bank" + num + "5"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 5)}
                value={this.props.plan.bank_names[num].channels[5]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 6 </label>
              <input
                name={"bank" + num + "6"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 6)}
                value={this.props.plan.bank_names[num].channels[6]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 7 </label>
              <input
                name={"bank" + num + "7"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 7)}
                value={this.props.plan.bank_names[num].channels[7]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 8 </label>
              <input
                name={"bank" + num + "8"}
                className="col-sm-6 edit-input"
                type="text"
                onChange={(event) => this.props.handleChannelNameChange(event.target.value,  num.toString(), 8)}
                value={this.props.plan.bank_names[num].channels[8]}
                maxLength={8}
              />
            </div>
          </div>
        );
      }
    }
    return <div className="panel-plan-inner">{edit_list}</div>;
  }
}
