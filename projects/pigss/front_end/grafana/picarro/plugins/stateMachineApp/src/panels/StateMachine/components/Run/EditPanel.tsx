import React, { Component, PureComponent, ReactText } from "react";
import Modal from "react-responsive-modal";
import { EditPanelOptions, Plan } from "../types";
import EditForm from "./EditForm";

interface State {
  initialized: boolean,
  modal_info: {},
  uistatus: {},
  plan: {
    bank_names: {
      [key: string]: {
        name: string,
        channels: {
          [key: number]: string
        }
      }
    }
  },
  show: boolean,
  prevState: {}
}

class EditPanel extends PureComponent<EditPanelOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
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
      show: false,
      prevState: {
        bank_names: {
          1: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: ""
            }
          },
          2: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: ""
            }
          },
          3: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: ""
            }
          },
          4: {
            name: "",
            channels: {
              1: "",
              2: "",
              3: "",
              4: "",
              5: "",
              6: "",
              7: "",
              8: ""
            }
          }
        }
      }
    };
    this.handleBankChange = this.handleBankChange.bind(this);
    this.handleChannelNameChange = this.handleChannelNameChange.bind(this);
  }

  

  banks: any;
  bank_list: any;

  componentDidMount = () => {
    // Store bank values in previous state
    this.setState({
      ...this.state,
      prevState: this.props.plan.bank_names
    });
  };

  handleBankChange = (value, num: string) => {
    this.setState({
      ...this.state,
      plan: {
        ...this.state.plan,
        bank_names: {
          ...this.state.plan.bank_names,
          [num]: {
            ...this.state.plan.bank_names[num],
            name: value
          }
        }
      }
    });
  };

  handleChannelNameChange(value, num: string, num2) {
    this.setState({
      ...this.state,
      plan: {
        ...this.state.plan,
        bank_names: {
          ...this.state.plan.bank_names,
          [num]: {
            ...this.state.plan.bank_names[num],
            channels: {
              ...this.state.plan.bank_names[num].channels,
              [num2]: value
            }
          }
        }
      }
    });
  }

  validateForm = bank_list => {
    let bankValue;
    for (const key in bank_list) {
      const bankNum = bank_list[key];
      bankValue = this.state.plan.bank_names[bankNum].name;
      if (bankValue.length < 1) {
        return false;
      } else if (bankValue.replace(/\s/g, "").length < 1) {
        return false;
      } else {
        for (let i = 1; i < 9; i++) {
          const chanValue = this.state.plan.bank_names[bankNum].channels[i];
          if (chanValue.length < 1) {
            return false;
          } else if (chanValue.replace(/\s/g, "").length < 1) {
            return false;
          }
        }
      }
    }
    return true;
  };

  handleSubmit = event => {
    event.preventDefault();
    this.bank_list = [];
    this.banks = this.props.uistatus.bank;
    for (const key in this.banks) {
      const value = this.banks[key];
      if (value === "READY") {
        this.bank_list.push(key);
      }
    }
    if (!this.validateForm(this.bank_list)) {
      this.setState({ show: true });
      return;
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

  handleClose = () => {
    this.setState({ show: false });
  };

  handleCancel = () => {
    // Set State to Previous Values
    this.setState({
      ...this.state,
      plan: {
        ...this.state.plan,
        bank_names: this.state.prevState
      }
    });
    this.props.ws_sender({ element: "edit_cancel" });
  };

  render() {
    const { show } = this.state;
    return (
      <div className="panel-edit">
        <h2 style={{ color: "#2f2f2f" }}>Edit Bank and Channel Names</h2>
        <form onSubmit={this.handleSubmit}>
          <EditForm
            handleBankChange={this.handleBankChange}
            handleChannelNameChange={this.handleChannelNameChange}
            uistatus={this.props.uistatus}
            plan={this.state.plan}
            ws_sender={this.props.ws_sender}
          />
          <div className="row text-center button-edit">
            <div className="col-sm-4">
              <button
                id={"submit-edit"}
                type="submit"
                className={"btn  btn-green btn-edit-panel btn-group-2"}
              >
                Ok
              </button>
            </div>
            <div className="col-sm-4">
              <button
                id={"cancel-btn"}
                type="button"
                onClick={this.handleCancel}
                className={"btn btn-cancel btn-edit-panel btn-group-2"}
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
        <Modal open={show} onClose={this.handleClose} center>
          <h2 style={{ color: "black" }}>Uh Oh!</h2>
          <p style={{ color: "black" }}>
            Each Label must be at least one character in length.
          </p>
        </Modal>
      </div>
    );
  }
}

export default EditPanel;
