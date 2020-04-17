import React, { Component, ReactText } from "react";
import ReactList from "react-list";
import { PlanSavePanelOptions, Plan } from "../types";
import { PlanService } from "../../api/PlanService";

interface State {
  fileName: string,
  fileNames: {},
  plan: Plan
}
class SavePanel extends Component<PlanSavePanelOptions, State> {
  constructor(props) {
    super(props)
    this.state = {
      fileName: "",
      fileNames: this.props.fileNames,
      plan: this.props.plan
    }
    // this.deleteFile = this.deleteFile.bind(this);
    // this.savePlan = this.savePlan.bind(this);
    this.updateFileName = this.updateFileName.bind(this)
  }

  componentDidMount() {
    const plan = this.props.getStateFromSavedData();
    this.setState({plan: plan})
  }

  updateFileName(e) {
    const plan = {...this.state.plan}
    plan.plan_filename = e.target.value
    this.setState({fileName: e.target.value, plan});
  }

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn btn-light w-100 btn-small"
          style={{ color: "black" }}
        >
          {this.state.fileNames[index]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e =>
            {
              this.props.deleteFile(this.state.fileNames[index]);
            }
          }
        >
          X
        </button>
      </div>
    </div>
  );
  render() {
    let length = Object.keys(this.props.fileNames).length

    const saveButtons = {
      
    }
    
    return (
      <div className="panel-save">
        <h2 style={{ color: "white" }}>Save Plan</h2>
        <div className="panel-save-inner">
          <form>
            <ReactList
              itemRenderer={this.renderItem}
              length={length}
              type={"uniform"}
            />
          </form>
        </div>
        <div className="col-sm-12" style={{ marginTop: "20px" }}>
          <input
            onChange={e => {
              this.updateFileName(e)
              // this.setState({fileName: e.target.value})
            }}
            maxLength={28}
            type="text"
            className="form-control input-large"
            style={{
              backgroundColor: "white",
              borderRadius: 3,
              color: "black",
              height: 35
            }}
            placeholder="Filename (without extension)"
          />
        </div>

        <div className="container" style={{ marginTop: "20px" }}>
          <div className="text-center">
            <button
              id="cancel-save"
              type="button"
              onClick={e =>
                this.props.updatePanel(0)
              }
              className={"btn btn-group-2 btn-cancel"}
            >
              Cancel
            </button>
            <button
              type="button"
              id="save-btn"
              onClick={e => {
                // this.savePlan();
                this.props.setModalInfo(true, `<div>Save file as ${this.state.fileName}?</div>`, 2, {
                  1: {
                    caption: "Save",
                    className: "btn btn-success btn-large",
                    response: {filename: this.state.fileName, plan: this.state.plan}
                  },
                  2: {
                    caption: "Cancel",
                    className: "btn btn-danger btn-large",
                    response: null
                  }
                }, 'save')
                
              }}
              className={"btn btn-group-2 btn-green"}
            >
              OK
            </button>
          </div>
        </div>
      </div>
    );
  }
}

export default SavePanel;
