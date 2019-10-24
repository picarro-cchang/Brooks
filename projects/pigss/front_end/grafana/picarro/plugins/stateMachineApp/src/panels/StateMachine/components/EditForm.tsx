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
    for (let key in this.banks) {
      let value = this.banks[key];
      if (value === "READY") {
        this.bank_list.push(key);
        edit_list.push(
          <div className="gf-form-group">
            <div className="row">
              <label className="edit-label"> Bank {key}</label>
              <input
                name={"bank" + key}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].name}
                maxLength={14}
              />
            </div>
            <div className="row">
              <label className="edit-label "> Channel 1 </label>
              <input
                name={"bank" + key + "1"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[1]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 2 </label>
              <input
                name={"bank" + key + "2"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[2]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 3 </label>
              <input
                name={"bank" + key + "3"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[3]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 4 </label>
              <input
                name={"bank" + key + "4"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[4]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 5 </label>
              <input
                name={"bank" + key + "5"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[5]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 6 </label>
              <input
                name={"bank" + key + "6"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[6]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 7 </label>
              <input
                name={"bank" + key + "7"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[7]}
                maxLength={8}
              />
            </div>
            <div className="row">
              <label className="edit-label"> Channel 8 </label>
              <input
                name={"bank" + key + "8"}
                className="col-sm-6 edit-input"
                type="text"
                defaultValue={this.state.plan.bank_names[key].channels[8]}
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
