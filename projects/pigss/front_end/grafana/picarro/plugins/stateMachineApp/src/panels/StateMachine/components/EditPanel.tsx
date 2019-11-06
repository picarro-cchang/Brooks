import React, { Component, PureComponent, ReactText } from "react";
import Modal from "react-responsive-modal";
import { EditPanelOptions } from "../types";
import { EditForm } from "./EditForm";

class EditPanel extends PureComponent<EditPanelOptions> {
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
    },
    show: false
  };
  constructor(props) {
    super(props);
  }

  banks: any;
  bank_list: any;

  validateForm = (bank_list, targets) => {
    let bankName, bankValue;
    const length = targets.length;
    for (let key in bank_list) {
      let bankNum = bank_list[key];
      bankName = "bank" + bankNum;
      bankValue = targets[bankName].value;
      if (bankValue.length < 1) {
        return false
      }
      else if (bankValue.replace(/\s/g, '').length < 1) {
        return false;
      }
      else
      {
        for (let i = 1; i < 9; i++) {
          const chanName = bankName + i;
          const chanValue = targets[chanName].value;
          if (chanValue.length < 1) {
            return false
          }
          else if (chanValue.replace(/\s/g, '').length < 1) {
            return false;
          }
        }
      }
    }
    return true
  };

  handClose = () => {
    this.setState({show: false})
  }

  handleSubmit = event => {
    event.preventDefault();
    let bankName, bankValue;
    this.bank_list = [];
    this.banks = this.props.uistatus.bank;
    for (let key in this.banks) {
      let value = this.banks[key];
      if (value === "READY") {
        this.bank_list.push(key);
      }
    }
    const targets = event.target;
    const length = targets.length;
    if (!this.validateForm(this.bank_list, targets)) {
      this.setState({show: true});
      return
    }
    for (let key in this.bank_list) {
      let bankNum = this.bank_list[key];
      bankName = "bank" + bankNum;
      bankValue = targets[bankName].value;
      const { bank_names } = { ...this.state.plan };
        const currentName = bank_names[bankNum];
        currentName.name = bankValue;
        this.setState({
          ...this.state.plan.bank_names,
          [bankNum]: { name: bankValue }
        });
      const { channels } = { ...this.state.plan.bank_names[bankNum] };
      const currentNames = channels;
      for (let i = 1; i < 9; i++) {
        const chanName = bankName + i;
        const chanValue = targets[chanName].value;
          currentNames[i] = chanValue;
          this.setState({
            ...this.state.plan.bank_names[bankNum].channels,
            [i]: chanValue
          });
      }
    }
    const channels1 = this.state.plan.bank_names[1].channels;
    const channels2 = this.state.plan.bank_names[2].channels;
    const channels3 = this.state.plan.bank_names[3].channels;
    const channels4 = this.state.plan.bank_names[4].channels;
    this.props.ws_sender({
      element: "edit_save",
      bank_names: {
        1: { name: this.state.plan.bank_names[1].name, channels: channels1 },
        2: { name: this.state.plan.bank_names[2].name, channels: channels2 },
        3: { name: this.state.plan.bank_names[3].name, channels: channels3 },
        4: { name: this.state.plan.bank_names[4].name, channels: channels4 }
      }
    });
  };
  render() {
    const {show} = this.state;
    return (
      <div className="panel-edit">
        <h2 style={{ color: "#2f2f2f" }}>Edit Bank and Channel Names</h2>
        <form onSubmit={this.handleSubmit} >
          <EditForm
            uistatus={this.props.uistatus}
            plan={this.props.plan}
            ws_sender={this.props.ws_sender}
          />
          <div className="row text-center button-edit">
            <div className="col-sm-4">
              <button
                  id={"submit-edit"}
                type="submit"
                className={"btn  btn-green btn-edit-panel btn-group-2"}>Ok</button>
            </div>
            <div className="col-sm-4">
              <button
                type="button"
                onClick={e => {
                  this.props.ws_sender({ element: "edit_cancel" });
                }}
                className={"btn btn-cancel btn-edit-panel btn-group-2"}
              >
                Cancel
              </button>
            </div>
          </div>

        </form>
        <Modal open={show} onClose={this.handClose} center >
          <h2 style={{color: "black"}}>Uh Oh!</h2>
          <p style={{color: "black"}}>Each Label must be at least one character in length.</p>
        </Modal>
      </div>
    );
  }
}

export default EditPanel;
