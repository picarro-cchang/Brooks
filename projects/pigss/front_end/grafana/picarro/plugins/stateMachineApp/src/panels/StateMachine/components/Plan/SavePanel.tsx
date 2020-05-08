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
    this.setFileName = this.setFileName.bind(this)
  }

  validatePlanName(fileName: string) {
    if (fileName.length <= 0) {
      this.props.setModalInfo(true, `<h4 style='color: black'>Invalid Plan Name length.</h4>`, 0, {}, 'validation')
      return false
    } else if (this.props.fileNames.includes(fileName)) {
      this.props.setModalInfo(true, `<h4 style='color: black'>Plan Name Already Taken.</h4>`, 0, {}, 'validation')
      return false
    }
    return true
  }

  savePlanFileName(fileName: string, plan: Plan) {
    const valid = this.validatePlanName(fileName)
    if(valid){
      this.props.setModalInfo(true, `<div>Save file as ${this.state.fileName}?</div>`, 2, {
        1: {
          caption: "Save",
          className: "btn btn-success btn-large",
          response: {filename: fileName, plan: plan}
        },
        2: {
          caption: "Cancel",
          className: "btn btn-danger btn-large",
          response: null
        }
      }, 'save')
    } else {
      
    }
  }


  setFileName(e) {
    const plan = {...this.state.plan}
    plan.plan_filename = e.target.value
    this.setState({fileName: e.target.value.replace(/\s/g, ''), plan});
  }

  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn btn-light w-100 btn-small"
          style={{ color: "black" }}
        >
          {this.props.fileNames[index]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e =>
            {
              this.props.deleteFile(this.props.fileNames[index]);
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
          id={'fileName'}
            onChange={e => {
              e.target.value = e.target.value.replace(/\s/g, '')
              this.setFileName(e)
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
              onClick={e => {this.savePlanFileName(this.state.fileName, this.state.plan)}}
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
