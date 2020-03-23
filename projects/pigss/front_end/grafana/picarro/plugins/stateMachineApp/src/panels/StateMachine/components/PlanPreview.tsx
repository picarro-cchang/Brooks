import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanLoadPanelOptions, Plan } from "./../types";

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


  render() {
    return (
      <div className="panel-save">
        Hello! Showing plan {this.props.plan.plan_filename}
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
