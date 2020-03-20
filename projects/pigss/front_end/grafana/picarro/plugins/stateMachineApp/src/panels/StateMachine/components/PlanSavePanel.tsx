import React, { PureComponent, ReactText } from "react";
import ReactList from "react-list";
import { PlanSavePanelOptions } from "./../types";
import { PlanService } from "../api/PlanService";

interface State {
  fileName: string,
  // isOverwritten: boolean
}
class PlanSavePanel extends PureComponent<PlanSavePanelOptions, State> {
  constructor(props) {
    super(props)
    this.state = {
      fileName: this.props.plan.plan_filename
    }
  }

  deleteFile(fileName: string) {
    PlanService.deleteFile(fileName).then((response: any) => {
      response.json().then((data: any) => {
        console.log(data)
      })
    })
  }
  renderItem = (index: number, key: ReactText) => (
    <div className="container" style={{ paddingTop: "5px" }} key={key}>
      <div className="btn-group d-flex" style={{ marginLeft: "0px" }}>
        <button
          type="button"
          className="btn btn-light w-100 btn-small"
          // onClick={e =>
            //set filename state to filename

            // this.props.ws_sender({
            //   element: "plan_save_filename",
            //   name: this.props.plan.plan_files[index + 1]
            // })
          // }
          style={{ color: "black" }}
        >
          {this.props.plan.plan_files[index + 1]}
        </button>
        <button
          type="button"
          className="btn btn-danger btn-small"
          onClick={e =>
            this.deleteFile(this.props.plan.plan_files[index+1])
            //Delete File
            //not going to actually delete file, but will have a boolean field, this will send a request to change it to false
          }
        >
          X
        </button>
      </div>
    </div>
  );
  render() {
    return (
      <div className="panel-save">
        <h2 style={{ color: "white" }}>Save Plan</h2>
        <div className="panel-save-inner">
          <form>
            <ReactList
              itemRenderer={this.renderItem}
              length={this.props.plan.num_plan_files}
              type={"uniform"}
            />
          </form>
        </div>
        <div className="col-sm-12" style={{ marginTop: "20px" }}>
          <input
            onChange={e =>
              this.setState({fileName: e.target.value})
            }
            maxLength={28}
            value={this.props.plan.plan_filename}
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
              type="button"
              onClick={e =>
                this.props.editPlan()
              }
              className={"btn btn-group-2 btn-cancel"}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={e => {
                this.props.updateFileName(false);
                this.props.planSaved(this.state.fileName);
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

export default PlanSavePanel;
