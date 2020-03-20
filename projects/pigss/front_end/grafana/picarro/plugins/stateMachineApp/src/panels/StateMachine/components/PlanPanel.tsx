import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanPanelOptions, PlanStep, Plan } from "./../types";
import { PlanService } from "./../api/PlanService";
import fs from "fs";

export interface State {
  refVisible: boolean;
  plan: Plan;
  isChanged: boolean;
  isLoaded: boolean;
  bankAdditionClicked: {};
  fileName: string;
}

class PlanPanel extends PureComponent<PlanPanelOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      bankAdditionClicked: {},
      isLoaded: false,
      refVisible: true,
      isChanged: this.props.isChanged,
      plan: {
        max_steps: 32,
        panel_to_show: 0,
        current_step: 1,
        focus: {
          row: 1,
          column: 1
        },
        last_step: 0,
        steps: {},
        num_plan_files: 0,
        plan_files: {},
        plan_filename: "",
        bank_names: {}
      },
      fileName: this.props.fileName
    };
    this.addToPlan = this.addToPlan.bind(this);
    this.getAvailableBanks = this.getAvailableBanks.bind(this);
    this.getLoadedPlan = this.getLoadedPlan.bind(this);
    this.updateFocus = this.updateFocus.bind(this);
  }

  shouldComponentUpdate(nextProps, nextState) {
    // if update works, it will update bankAdditionClicked
    if (this.props.bankAddition !== nextProps.bankAddition) {
      this.setState({
        bankAdditionClicked: nextProps.bankAddition
      });
      if (nextProps.bankAddition.bank != undefined) {
        const bank = nextProps.bankAddition.bank;
        const channel = nextProps.bankAddition.channel;
        const row = this.state.plan.focus.row;
        this.changeChannelstoProperFormat(bank, channel, row);
      }
    }
    return true;
  }

  componentDidMount() {
    this.getLoadedPlan();
  }

  getLoadedPlan() {
    // Works with TEST data for now, since no backend service
    if (this.state.fileName) {
      // GET steps from plan
      PlanService.getFileData(this.state.fileName).then((response: any) => {
        response.json().then((data: any) => {
          this.setState({ plan: data });
        });
      });
    }
  }

  // TODO
  saveFile() {
    // PlanService.saveFile(this.state.)
    // Move to Save Panel
    this.props.savePlan();
  }

  // TODO
  saveFileAs() {
    // saveAs, modal for Are you sure?
    PlanService.saveFileAs(this.state.plan, this.state.plan.plan_filename);
    console.log("here");
  }

  // TODO
  clearPlan() {}

  // TODO
  deleteFile() {}

  getAvailableBanks() {
    const availableBanks = [];
    if (("bank" in this.props.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.props.uistatus as any).bank.hasOwnProperty(i)) {
          availableBanks.push(i);
        }
      }
    }
    return availableBanks;
  }

  addToPlan(bank_config, reference: number) {
    let row = this.state.plan.focus.row;
    const col = this.state.plan.focus.column;
    let duration;
    if (row >= this.state.plan.max_steps && col == 2) {
      // error
    }
    if (col == 2) {
      row += 1;
    }
    if (row <= this.state.plan.last_step) {
      duration = this.state.plan[row].duration;
    } else {
      duration = 0;
    }

    const bank_step = {
      banks: bank_config,
      reference,
      duration
    };

    const plan = { ...this.state.plan };
    plan.steps[row] = bank_step;

    if (this.state.plan.last_step < row) {
      plan.last_step = row;
    }
    plan.focus = {
      row,
      column: 2
    };
    this.setState({ plan });
  }

  updateFocus(row: number, column: number) {
    const plan = { ...this.state.plan };
    if (row <= this.state.plan.last_step || row == this.state.plan.last_step) {
      plan.focus = {
        row,
        column
      };
    }
    this.setState({ plan });
  }

  updateDuration(row: number, duration: number) {
    const plan = { ...this.state.plan };
    plan.steps[row].duration = duration;
    this.setState({ plan });
  }

  updateCurrentStep(row: number) {
    const plan = { ...this.state.plan };
    plan.current_step = row;
    this.setState({ plan });
  }

  insertRow() {
    const all_banks = this.getAvailableBanks();
    const row = this.state.plan.focus.row;
    const col = this.state.plan.focus.column;
    const num_steps = this.state.plan.last_step;
    const plan = { ...this.state.plan };
    if (num_steps < this.state.plan.max_steps) {
      for (let i = this.state.plan.last_step; i > row - 1; i -= 1) {
        const s = this.state.plan.steps[i];
        // insert the plan 1 row down
        plan.steps[i + 1] = s;
      }
      const bank_config = {};
      for (const b in all_banks) {
        bank_config[all_banks[b]] = { clean: 0, chan_mask: 0 };
      }
      plan.steps[row] = {
        banks: bank_config,
        reference: 0,
        duration: 0
      };
      plan.last_step = num_steps + 1;
    }
    plan.focus = {
      row,
      column: col
    };
    this.setState({ plan });
  }

  changeChannelstoProperFormat(bank, channel, row) {
    const all_banks = this.getAvailableBanks();
    const bank_config = {};
    for (const b in all_banks) {
      bank_config[all_banks[b]] = { clean: 0, chan_mask: 0 };
    }
    if (bank == 0) {
      this.addToPlan(bank_config, 1);
    } else {
      if (channel == 0) {
        bank_config[bank].clean = 1;
        this.addToPlan(bank_config, 0);
      } else {
        bank_config[bank].chan_mask = 1 << (channel - 1);
        this.addToPlan(bank_config, 0);
      }
    }
  }

  focusComponent: any = null;
  focusTimer: any = null;

  manageFocus = (component: any) => {
    // Manages focus by storing the component which is to receive focus
    //  and calling its focus() method after a short timeout. Multiple
    //  calls to manageFocus during the expiry of the timer will cause
    //  only the last component to receive the focus. This prevents
    //  oscillations in which a cycle of components receive focus in
    //  quick succession.
    if (this.focusTimer !== null) {
      clearTimeout(this.focusTimer);
    }
    this.focusComponent = component;
    this.focusTimer = setTimeout(() => {
      this.focusComponent.focus();
      this.focusTimer = null;
    }, 200);
  };

  makePlanRow = (row: number) => {
    let portString = "";
    let durationString = "";
    if (this.state.plan.last_step >= row) {
      const planRow = this.state.plan.steps[row] as PlanStep;
      if (planRow.reference != 0) {
        portString = "Reference";
      } else {
        for (const bank in planRow.banks) {
          if (planRow.banks.hasOwnProperty(bank)) {
            const bank_name = this.props.plan.bank_names[bank].name;
            const bank_config = planRow.banks[bank];
            if (bank_config.clean != 0) {
              portString = `Clean ${bank_name}`;
              break;
            } else if (bank_config.chan_mask != 0) {
              const mask = bank_config.chan_mask;
              // Find index of first set bit using bit-twiddling hack
              const channel = (mask & -mask).toString(2).length;
              const ch_name = this.props.plan.bank_names[bank].channels[
                channel
              ];
              portString = bank_name + ", " + ch_name;
              break;
            }
          }
        }
      }
      if (planRow.duration !== 0) {
        durationString = `${planRow.duration}`;
      }
    }

    return (
      <div className="gf-form-inline" key={row}>
        {row < 10 ? (
          <label
            className="col-sm-1 panel-plan-text"
            style={{ fontSize: "17px", marginTop: "5px" }}
          >
            {row + ". "}
          </label>
        ) : (
          <label
            className="col-sm-1 panel-plan-text"
            style={{
              marginLeft: "-7px",
              marginRight: "7px",
              fontSize: "17px",
              marginTop: "5px"
            }}
          >
            {row + ". "}
          </label>
        )}
        <div className="col-sm-6 col-bank-name">
          <input
            ref={input =>
              input &&
              this.state.plan.focus.row === row &&
              this.state.plan.focus.column === 1 &&
              this.manageFocus(input)
            }
            type="text"
            className="form-control plan-input panel-plan-text"
            id={"plan-port-" + row}
            onFocus={e => {
              // this.changeChannelstoProperFormat(bank, channel, row);
              this.updateFocus(row, 1);
            }}
            onChange={e => {
              this.props.updateFileName(true);
            }}
            style={{ maxWidth: "90%", float: "left", marginLeft: "2px" }}
            value={portString}
            placeholder="Select port"
          />
        </div>
        <div className="col-sm-3" style={{ paddingLeft: "0px" }}>
          <input
            ref={input =>
              input &&
              this.state.plan.focus.row === row &&
              this.state.plan.focus.column === 2 &&
              this.manageFocus(input)
            }
            onChange={e => {
              this.props.updateFileName(true);
              this.updateDuration(row, Number(e.target.value));
            }}
            onFocus={e => {
              this.updateFocus(row, 2);
            }}
            maxLength={8}
            minLength={1}
            type="text"
            className="form-control input-small plan-input panel-plan-text"
            id={"plan-duration-" + row}
            style={{ maxWidth: "100%" }}
            value={durationString}
            placeholder="Duration"
          />
        </div>
        <label
          className="panel-plan-text"
          style={{ marginLeft: "-15px", paddingRight: "5px" }}
        >
          s
        </label>
        <label className="col-sm-1 radio-btn">
          <input
            type="radio"
            id={"plan-row-" + row}
            checked={row == this.state.plan.current_step}
            onChange={e => this.updateCurrentStep(row)}
            style={{ maxWidth: "100%" }}
          />
          <span className="checkmark"></span>
        </label>
      </div>
    );
  };

  renderItem = (index: number, key: ReactText) => (
    <div key={key}>{this.makePlanRow(index + 1)}</div>
  );

  render() {
    const file_name = this.state.plan.plan_filename;

    return (
      <div>
        <div className="panel-plan">
          <h2 className="panel-plan-text">Schedule</h2>
          <span
            className="cancel panel-plan-text"
            id="cancel-x"
            onClick={e => {
              this.props.ws_sender({ element: "plan_cancel" });
            }}
          ></span>
          <h6 className="panel-plan-text">
            Please click on available channels to set up a schedule, then click
            on the radio button to select starting position.
          </h6>
          {this.state.plan.plan_filename && !this.state.isChanged ? (
            <div>
              <h6 className="panel-plan-text">
                Currently viewing File:{" "}
                <span style={{ color: "white" }}>{file_name}</span>
              </h6>
            </div>
          ) : (
            <h6 style={{ color: "white" }}>
              Currently not viewing a saved file
            </h6>
          )}
          <div className="panel-plan-inner">
            <form>
              <ReactList
                itemRenderer={this.renderItem}
                length={this.state.plan.max_steps}
                type={"uniform"}
              />
            </form>
          </div>
          <div className="container">
            <div className="row text-center btn-row-1">
              <div className="col-sm-3">
                <button
                  type="button"
                  id="insert-btn"
                  disabled={
                    this.state.plan.focus.row > this.state.plan.last_step
                  }
                  onClick={e => {
                    this.setState({ isChanged: true });
                    this.insertRow();
                  }}
                  className={"btn btn-block btn-group"}
                >
                  Insert
                </button>
              </div>
              <div className="col-sm-3">
                <button
                  type="button"
                  id="save-btn"
                  onClick={e => {
                    // this.props.ws_sender({ element: "plan_save" })
                    this.saveFile();
                  }}
                  className={"btn btn-block btn-light btn-group"}
                >
                  Save
                </button>
              </div>

              <div className="col-sm-3">
                <button
                  type="button"
                  id="load-btn"
                  onClick={e => {
                    // this.props.ws_sender({ element: "plan_load" })
                    // this.loadFile()
                    this.props.loadFile();
                  }}
                  className={"btn btn-block btn-light btn-group"}
                >
                  Load
                </button>
              </div>
            </div>
            <div className="row btn-row-2">
              <div className="col-sm-3">
                <button
                  type="button"
                  id="delete-btn"
                  disabled={
                    this.state.plan.focus.row > this.state.plan.last_step
                  }
                  onClick={e => {
                    this.props.updateFileName(true);
                    // Delete File... NECESSARY? IDK
                  }}
                  className={"btn btn-block btn-cancel btn-group"}
                >
                  Delete
                </button>
              </div>
              <div className="col-sm-3">
                <button
                  type="button"
                  id="clear-btn"
                  disabled={
                    this.state.plan.focus.row > this.state.plan.last_step
                  }
                  onClick={e => {
                    this.props.updateFileName(true);
                    // Clear Plan Steps State
                    // this.clearPlan();
                  }}
                  className={"btn btn-block btn-cancel btn-group"}
                >
                  Clear
                </button>
              </div>

              <div className="col-sm-3">
                <button
                  type="button"
                  id="ok-btn"
                  onClick={e => {
                    // Save State as JSON Object, send to Service
                    this.saveFileAs();
                  }}
                  className={"btn btn-block btn-green btn-group"}
                >
                  Save As
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default PlanPanel;
