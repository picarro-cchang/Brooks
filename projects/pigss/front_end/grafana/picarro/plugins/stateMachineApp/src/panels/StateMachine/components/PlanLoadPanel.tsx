import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanLoadPanelOptions, Plan } from "./../types";

// changes.....
// LOAD file names from service (?) or we can still have filenames in props, but now when filename gets clicked, it
// gets info from service. If plan is being selected for run, we add it to props (in backend, perform same function to 'load a plan')
// if plan is being selected for editing, we pass plan file name and info to state of edit panel
interface State {
  plan: Plan;
}
class PlanLoadPanel extends PureComponent<PlanLoadPanelOptions, State> {
  constructor(props) {
    super(props) 
    this.state = {
      plan: this.props.plan,
    }
  }

  

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn w-100 btn-small"
          onClick={e => {
            this.props.updateFileName(false);
            this.props.loadPlan(this.state.plan.plan_files[index + 1])
          }}
          style={{ color: "black" }}
        >
          {this.state.plan.plan_files[index + 1]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e => {
            this.props.deleteFile(this.state.plan.plan_files[index+1]);
          }}
        >
          X
        </button>
      </div>
    </div>
  );

  render() {
    return (
      <div className="panel-save">
        <h2 style={{ color: "white" }}>Load Plan</h2>
        <div className="panel-save-inner">
          <form>
            <ReactList
              itemRenderer={this.renderItem}
              length={this.props.plan.num_plan_files}
              type={"uniform"}
            />
          </form>
        </div>
        <div className="container" style={{ marginTop: "20px" }}>
          <div className="row text-center">
            <div className="col-sm-12">
              <button
                id={"cancel"}
                type="button"
                onClick={e =>
                  this.props.updatePanel(0)
                }
                className={"btn btn-group-2 btn-cancel"}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default PlanLoadPanel;
