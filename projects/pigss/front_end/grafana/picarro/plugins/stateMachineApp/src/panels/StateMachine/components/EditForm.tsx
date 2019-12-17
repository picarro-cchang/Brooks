import React, { Component, PureComponent, ReactText } from "react";
import { EditPanelOptions } from "../types";

export class EditForm extends Component<EditPanelOptions> {
  state = {
    initialized: false,
    modal_info: {
      show: false,
      html: "",
      num_buttons: 0,
      buttons: {}
    },
    uistatus: {},
    plan: {
      bank_names: this.props.plan.bank_names
    }
  };
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
                defaultValue={this.state.plan.bank_names[num].name}
                maxLength={14}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 1 </label>
              <input
                name={"bank" + num + "1"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[1]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 2 </label>
              <input
                name={"bank" + num + "2"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[2]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 3 </label>
              <input
                name={"bank" + num + "3"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[3]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 4 </label>
              <input
                name={"bank" + num + "4"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[4]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 5 </label>
              <input
                name={"bank" + num + "5"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[5]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 6 </label>
              <input
                name={"bank" + num + "6"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[6]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 7 </label>
              <input
                name={"bank" + num + "7"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[7]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 8 </label>
              <input
                name={"bank" + num + "8"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[num].channels[8]}
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
