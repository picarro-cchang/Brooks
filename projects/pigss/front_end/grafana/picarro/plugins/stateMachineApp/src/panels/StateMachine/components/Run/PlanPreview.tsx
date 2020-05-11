import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import {
  LoadPanelCommandOptions,
  Plan,
  PlanStep,
  PreviewPanelOptions,
} from "../types";

interface State {
  plan: Plan;
}
class PlanPreview extends PureComponent<PreviewPanelOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
    };
  }

  makePlanRow = (row: number) => {
    let portString = "";
    let durationString = "";
    const planRow = this.props.plan.steps[row] as PlanStep;
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
            const ch_name = this.props.plan.bank_names[bank].channels[channel];
            const bankNum = Number(bank);
            const portNumber = (bankNum - 1) * 8 + channel;
            portString = portNumber + ": " + ch_name;
            break;
          }
        }
      }
    }
    if (planRow.duration !== 0) {
      durationString = `${planRow.duration}`;
    }

    return (
      <div className="gf-form-inline" key={row}>
        <div
          className="panel-plan-text"
          style={{ fontSize: "17px", marginTop: "5px" }}
        >
          {row < 10 ? (
            <>{row + ". "}</>
          ) : (
            <span
              className="panel-plan-text"
              style={{
                marginLeft: "-7px",
                marginRight: "7px",
                marginTop: "5px",
                fontSize: "17px",
              }}
            >
              {row + ". "}
            </span>
          )}
          {portString} Duration: {durationString}
        </div>
      </div>
    );
  };

  renderItem = (index: number, key: ReactText) => (
    <div key={key}>{this.makePlanRow(index + 1)}</div>
  );

  render() {
    return (
      <div className="panel-plan-preview">
        <h4>Plan: {this.props.plan.plan_filename}</h4>
        <h6>
          Press Ok to continue with this plan, or Cancel to choose another.
        </h6>
        <div className="panel-preview-inner">
          <div style={{ marginLeft: "5px" }}>
            <ReactList
              itemRenderer={this.renderItem}
              length={this.props.plan.last_step}
              type={"uniform"}
            />
          </div>
        </div>
        <div className="row btn-row-2">
          <div>
            <button
              id={"cancel-load-plan"}
              className={"btn btn-block btn-cancel btn-group-preview"}
              onClick={(e) => {
                this.props.ws_sender({
                  element: "filename_cancel",
                });
                this.props.cancelLoadPlan();
                this.props.updatePanel(1);
              }}
            >
              Cancel
            </button>
          </div>
          <div>
            <button
              className={"btn btn-block btn-green btn-group-preview"}
              onClick={(e) => {
                this.props.ws_sender({
                  element: "filename_ok",
                });
                this.props.setModalInfo(
                  true,
                  `<div>Load File ${this.state.plan.plan_filename} for running?</div>`,
                  2,
                  {
                    1: {
                      caption: "Ok",
                      className: "btn btn-success btn-large",
                      response: {
                        plan: this.state.plan,
                        name: this.state.plan.plan_filename,
                      },
                    },
                    2: {
                      caption: "Cancel",
                      className: "btn btn-danger btn-large",
                      response: null,
                    },
                  },
                  "loadPlan"
                );
              }}
            >
              Ok
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default PlanPreview;
