import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanLoadPanelOptions } from "./../types";

class PlanLoadPanel extends PureComponent<PlanLoadPanelOptions> {
  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn w-100 btn-small"
          onClick={e => {
            this.props.updateFileName(false);
            this.props.ws_sender({
              element: "plan_load_filename",
              name: this.props.plan.plan_files[index + 1]
            });
          }}
          style={{ color: "black" }}
        >
          {this.props.plan.plan_files[index + 1]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e => {
            this.props.ws_sender({
              element: "plan_delete_filename",
              name: this.props.plan.plan_files[index + 1]
            });
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
                type="button"
                onClick={e =>
                  this.props.ws_sender({ element: "plan_load_cancel" })
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