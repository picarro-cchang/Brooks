import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanLoadPanelEditOptions, Plan } from "./../types";
import { PlanService } from "../api/PlanService";

// changes.....
// LOAD file names from service (?) or we can still have filenames in props, but now when filename gets clicked, it
// gets info from service. If plan is being selected for run, we add it to props (in backend, perform same function to 'load a plan')
// if plan is being selected for editing, we pass plan file name and info to state of edit panel

interface State {
  plan: Plan;
}

class PlanLoadEditPanel extends PureComponent<PlanLoadPanelEditOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan
    };
    this.getFileNames = this.getFileNames.bind(this);
  }

  getFileNames() {
    PlanService.getFileNames().then((response: any) => {
      response.json().then((fileNames: any) => {
        const length = Object.keys(fileNames).length;

        this.setState({
          plan: {
            ...this.state.plan,
            plan_files: fileNames,
            num_plan_files: length
          }
        });
      });
    });
  }

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn w-100 btn-small"
          onClick={e => {
            this.props.updateFileName(false);
            this.props.getFileName(this.state.plan.plan_files[index + 1]);
          }}
          style={{ color: "black" }}
        >
          {this.state.plan.plan_files[index + 1]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e => {
            // ADD FUNCTION TO DELETE FROM SERVICE
            // this.props.ws_sender({
            // element: "plan_delete_filename",
            // name: this.props.plan.plan_files[index + 1]
            // });
          }}
        >
          X
        </button>
      </div>
    </div>
  );

  render() {
    this.getFileNames();
    return (
      <div className="panel-save">
        <h2 style={{ color: "white" }}>Load Plan</h2>
        <div className="panel-save-inner">
          <form>
            <ReactList
              itemRenderer={this.renderItem}
              length={this.state.plan.num_plan_files}
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
                onClick={e => this.props.editPlan()}
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

export default PlanLoadEditPanel;
