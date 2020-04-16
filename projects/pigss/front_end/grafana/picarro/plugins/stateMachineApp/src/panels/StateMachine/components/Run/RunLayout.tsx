import React, { PureComponent } from "react";
import BankPanel from "./BankPanel";
import CommandPanel from "./CommandPanel";
import PlanLoadPanel from "./PlanLoadPanel";
import PlanPreview from "./PlanPreview";
import { PanelTypes, RunLayoutProps, Plan } from "../types";
import EditPanel from "./EditPanel";
import { PlanService } from "../../api/PlanService";
import { threadId } from "worker_threads";

interface State {
    plan: Plan, 
    fileNames: string[],
    panel_to_show: number,
    loadedPlanFilename: string
}

export class RunLayout extends PureComponent<RunLayoutProps, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
      fileNames: this.props.fileNames,
      panel_to_show: 0,
      loadedPlanFilename: ""
    }
    this.updatePanelToShow = this.updatePanelToShow.bind(this);
    // this.loadPlan = this.loadPlan.bind(this);
    this.cancelLoadPlan = this.cancelLoadPlan.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
    this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
  }

  getPlanFromFileName(filename: string) {
    PlanService.getFileData(filename).then((response: any) => 
      response.json().then(data => {
        console.log(`Getting Plan from Filename ${filename}! `, data["details"]);
        this.setState({plan: data["details"]})
        this.setState({
          loadedPlanFilename: filename,
          panel_to_show: 3
        });
      }))
  }

  deleteFile(fileName) {
    PlanService.deleteFile(fileName).then((response: any) => 
    response.json().then(data => {
      console.log("Plan Deleted! ", data)
      //TODO: need to refresh plan file names
    })
  );
  }

  updatePanelToShow(panel: number) {
    this.setState({panel_to_show: panel})
  } 

  cancelLoadPlan(){
    let plan = {
      max_steps: 32,
      panel_to_show: 0,
      current_step: 1,
      focus: { row: 0, column: 0 },
      last_step: 0,
      steps: {},
      num_plan_files: 0,
      plan_files: {},
      plan_filename: "",
      bank_names: {
        1: {
          name: "",
          channels: {
            1: "Port 1",
            2: "Port 2",
            3: "Port 3",
            4: "Port 4",
            5: "Port 5",
            6: "Port 6",
            7: "Port 7",
            8: "Port 8"
          }
        },
        2: {
          name: "",
          channels: {
            1: "Port 9",
            2: "Port 10",
            3: "Port 11",
            4: "Port 12",
            5: "Port 13",
            6: "Port 14",
            7: "Port 15",
            8: "Port 16"
          }
        },
        3: {
          name: "",
          channels: {
            1: "Port 17",
            2: "Port 18",
            3: "Port 19",
            4: "Port 20",
            5: "Port 21",
            6: "Port 22",
            7: "Port 23",
            8: "Port 24"
          }
        },
        4: {
          name: "",
          channels: {
            1: "Port 25",
            2: "Port 26",
            3: "Port 27",
            4: "Port 28",
            5: "Port 29",
            6: "Port 30",
            7: "Port 31",
            8: "Port 32"
          }
        }
      }
    }
    //set to previous state
    this.setState({plan})
  }

  render() {
    let left_panel;
    switch (this.state.panel_to_show) {
      case PanelTypes.NONE:
        left_panel = (
          <CommandPanel
            plan={this.state.plan}
            uistatus={this.props.uistatus}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
            layoutSwitch={this.props.layoutSwitch}
          />
        );
        break;
      case PanelTypes.LOAD:
        left_panel = (
          <PlanLoadPanel
            plan={this.state.plan}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
            // deleteFile={this.deleteFile}
            // loadPlan={this.loadPlan}
            fileNames={this.props.fileNames}
            cancelLoadPlan={this.cancelLoadPlan}
            deleteFile={this.deleteFile}
            getPlanFromFileName={this.getPlanFromFileName}
          />
        );
        break;
      case PanelTypes.EDIT:
        left_panel = (
          <EditPanel
            plan={this.state.plan}
            uistatus={this.props.uistatus}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
          />
        );
        break;
      case PanelTypes.PREVIEW:
        left_panel = (
          <PlanPreview
            plan={this.state.plan}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
            // deleteFile={this.deleteFile}
            // loadPlan={this.loadPlan}
            fileNames={this.state.fileNames}
            cancelLoadPlan={this.cancelLoadPlan}
          />
        )
    }

    const bankPanels = [];
    if (("bank" in this.props.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.props.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanels.push(
            <div>
              <BankPanel
                plan={this.state.plan}
                bank={i}
                key={i}
                uistatus={this.props.uistatus}
                ws_sender={this.props.ws_sender}
              />
            </div>
          );
        }
      }
    }

    return (
      <div style={{ textAlign: "center" }}>
            
        <div className="container-fluid">
          <div className="row justify-content-md-center">
            <div className="col-sm-3" style={{ height: "100%" }}>
              {left_panel}
            </div>
            <div
              className="col-sm-9"
              style={{ display: "grid", gridTemplateColumns: "1fr" }}
            >
                <div
                  style={{
                    padding: "10px",
                    gridRowStart: "1",
                    gridColumnStart: "1"
                  }}
                >
                  {bankPanels}
                </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
export default RunLayout
