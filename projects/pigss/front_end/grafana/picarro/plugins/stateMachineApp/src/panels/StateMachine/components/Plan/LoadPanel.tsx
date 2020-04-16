import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { LoadPanelOptions, Plan } from "../types";
import { throws } from "assert";

interface State {
  plan: Plan;
  fileNames: any[]
}

class LoadPanel extends PureComponent<LoadPanelOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
      fileNames: this.props.fileNames
    };
  }

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          id={"plan-filename-"+ (index + 1)}
          className="btn w-100 btn-small"
          onClick={e => {
            this.props.updateFileName(false);
            this.props.getPlanFromFileName(this.state.fileNames[index]);
          }}
          style={{ color: "black" }}
        >
          {this.state.fileNames[index]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e => {
            this.props.deleteFile(this.state.fileNames[index]);
          }}
        >
          X
        </button>
      </div>
    </div>
  );

  render() {
    let length = this.props.fileNames.length
    return (
      <div className="panel-save">
        <h2 style={{ color: "white" }}>Load Plan</h2>
        <div className="panel-save-inner">
          <form>
            <ReactList
              itemRenderer={this.renderItem}
              length={length}
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
                onClick={e => this.props.updatePanel(0)}
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

export default LoadPanel;
