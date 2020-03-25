import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanLoadPanelOptions, Plan,PlanStep } from "./../types";

interface State {
  plan: Plan;
}
class PlanPreviewPanel extends PureComponent<PlanLoadPanelOptions, State> {
  constructor(props) {
    super(props) 
    this.state = {
      plan: this.props.plan,
    }
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
            const ch_name = this.props.plan.bank_names[bank].channels[
              channel
            ];
            let bankNum = Number(bank)
            let portNumber = (bankNum - 1)*8 + channel
            portString = portNumber + ": " + ch_name;
            break;
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
          <span
            className="form-control plan-input panel-plan-text"
            id={"plan-port-" + row}
            style={{ maxWidth: "90%", float: "left", marginLeft: "2px" }}
          >
          {portString}
          </span>
        </div>
        <div className="col-sm-3" style={{ paddingLeft: "0px" }}>
          <span
            className="form-control input-small plan-input panel-plan-text"
            id={"plan-duration-" + row}
            style={{ maxWidth: "100%" }}
          >
          {durationString}
          </span>
        </div>
        <label
          className="panel-plan-text"
          style={{ marginLeft: "-15px", paddingRight: "5px" }}
        >
          s
        </label>
      </div>
    );
  };

  renderItem = (index: number, key: ReactText) => (
    <div key={key}>{this.makePlanRow(index + 1)}</div>
  );

  render() {
    return (
      <div className="panel-save">
        Hello! Showing plan {this.props.plan.plan_filename}
        <div className="panel-plan-inner">
            <form>
              <ReactList
                itemRenderer={this.renderItem}
                length={this.props.plan.last_step}
                type={"uniform"}
              />
            </form>
          </div>
        <button
            onClick={e => this.props.updatePanel(0)}
        >
            Ok
        </button>
        <button
            onClick={e => this.props.updatePanel(0)}
        >
            Cancel
        </button>
      </div>
    );
  }
}

export default PlanPreviewPanel;
