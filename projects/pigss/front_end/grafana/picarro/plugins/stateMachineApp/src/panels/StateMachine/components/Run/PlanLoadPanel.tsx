import React, { Component, ReactText } from "react";
import ReactList from "react-list";
import { LoadPanelCommandOptions, Plan } from "../types";
import { stringToJsRegex } from "@grafana/data";

interface State {
  plan: Plan;
  fileNames: {};
}
class PlanLoadPanel extends Component<LoadPanelCommandOptions, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
      fileNames: this.props.fileNames,
    };
  }

  shouldComponentUpdate(nextProps) {
    if (this.props.fileNames !== nextProps.fileNames) {
      console.log("UPDATE FILENAMES");
      this.setState({
        fileNames: nextProps.fileNames,
      });
    }
    return true;
  }

  isDisabled(file: string) {
    if (file == this.props.loadedFileName) {
      return true;
    }
    return false;
  }

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn w-100 btn-small"
          disabled={this.isDisabled(
            this.props.fileNames[Object.keys(this.props.fileNames)[index]]
          )}
          onClick={(e) => {
            this.props.ws_sender({
              element: "load_filename",
            });
            this.props.getPlanFromFileName(
              this.props.fileNames[Object.keys(this.props.fileNames)[index]]
            );
          }}
          style={{ color: "black" }}
        >
          {this.props.fileNames[Object.keys(this.props.fileNames)[index]]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          disabled={this.isDisabled(
            this.props.fileNames[Object.keys(this.props.fileNames)[index]]
          )}
          onClick={(e) => {
            this.props.deleteFile(
              this.props.fileNames[Object.keys(this.props.fileNames)[index]],
              Number(Object.keys(this.props.fileNames)[index])
            );
          }}
        >
          X
        </button>
      </div>
    </div>
  );

  render() {
    const length = Object.keys(this.props.fileNames).length;
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
                onClick={(e) => {
                  this.props.updatePanel(0);
                  this.props.ws_sender({
                    element: "load_cancel",
                  });
                }}
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
