import React, { Component, PureComponent } from "react";
import { CommandPanelOptions, Plan } from "./../types";

interface State {
  plan: Plan;
}
class CommandPanel extends PureComponent<CommandPanelOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
    };
  }
  classNameOpt = {
    DISABLED: "",
    READY: "btn-outline-success",
    ACTIVE: "btn-green",
  };

  getDisabled = (element: string): boolean => {
    let disabled = true;
    const status_dict = this.props.uistatus as any;
    if (element in status_dict) {
      disabled = status_dict[element] === "DISABLED";
    }
    return disabled;
  };

  getClassNameOpt = (element: string): string => {
    let classNames = "";
    const status_dict = this.props.uistatus as any;
    if (element in status_dict) {
      classNames = (this.classNameOpt as any)[status_dict[element]];
    }
    return classNames;
  };

  render() {
    return (
      <div className="panel-command">
        <div style={{ width: "100%", marginTop: 20 }}>
          <div
            className="grid-command"
            style={{
              display: "grid",
              gridTemplateColumns: "4rem 4rem 4rem 4rem 4rem 4rem",
              gridGap: 5,
              padding: 20,
            }}
          >
            <button
              id={"standby"}
              onClick={(e) => {
                this.props.ws_sender({ element: "standby" });
              }}
              disabled={this.getDisabled("standby")}
              value="standby"
              className={
                "btn btn-large btn-command btn-1-3 " +
                this.getClassNameOpt("standby")
              }
            >
              Standby
            </button>
            <button
              id={"identify"}
              onClick={(e) => this.props.ws_sender({ element: "identify" })}
              disabled={this.getDisabled("identify")}
              value="identify"
              className={
                "btn btn-large btn-command btn-1-3 " +
                this.getClassNameOpt("identify")
              }
            >
              Identify Available Channels
            </button>

            <button
              id={"edit-plan"}
              onClick={(e) => {
                this.props.layoutSwitch();
              }}
              disabled={this.getDisabled("plan")}
              value="plan"
              className={
                "btn btn-large btn-command btn-edit-plan " +
                this.getClassNameOpt("plan")
              }
            >
              Edit Plan
            </button>
            <button
              id={"load-plan"}
              onClick={(e) => {
                this.props.ws_sender({ element: "load" });
              }}
              disabled={this.getDisabled("load")}
              value="load"
              className={
                "btn btn-large btn-command btn-load " +
                this.getClassNameOpt("load")
              }
            >
              Load Plan
            </button>
            <button
              id={"run-channel"}
              onClick={(e) => this.props.ws_sender({ element: "run" })}
              disabled={this.getDisabled("run")}
              value="run"
              className={
                "btn btn-large btn-command btn-run-single " +
                this.getClassNameOpt("run")
              }
            >
              Single Port
            </button>
            <button
              id={"run-plan"}
              onClick={(e) => {
                this.props.ws_sender({ element: "plan_run" });
              }}
              disabled={this.getDisabled("plan_run")}
              value="plan_run"
              className={
                "btn btn-large btn-command btn-run " +
                this.getClassNameOpt("plan_run")
              }
            >
              Run Plan
            </button>
            <button
              id={"loop-plan"}
              onClick={(e) => {
                const name = this.props.plan.plan_filename;
                const plan = this.props.plan.current_step;
                this.props.ws_sender({ element: "plan_loop" });
              }}
              disabled={this.getDisabled("plan_loop")}
              value="plan_loop"
              className={
                "btn btn-large btn-command btn-run-loop " +
                this.getClassNameOpt("plan_loop")
              }
            >
              Loop Plan
            </button>
            <button
              id={"reference"}
              onClick={(e) => this.props.ws_sender({ element: "reference" })}
              disabled={this.getDisabled("reference")}
              value="reference"
              className={
                "btn btn-large btn-command btn-1-3 " +
                this.getClassNameOpt("reference")
              }
            >
              Reference
            </button>
            <button
              id={"edit-labels"}
              value="edit"
              className={"btn btn-large btn-edit btn-danger"}
              onClick={(e) => {
                this.props.ws_sender({ element: "edit" });
              }}
              disabled={this.getDisabled("edit")}
            >
              Edit Labels
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default CommandPanel;
