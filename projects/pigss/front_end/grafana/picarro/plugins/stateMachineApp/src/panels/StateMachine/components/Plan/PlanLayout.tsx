import React, { PureComponent } from "react";
import BankPanel from "./BankPanel";
import LoadPanel from "./LoadPanel";
import PlanPanel from "./PlanPanel";
import SavePanel from "./SavePanel";
import deepmerge from "deepmerge";
import { PlanLayoutProps, Plan, PlanPanelTypes } from "../types";
import { PlanService } from "../../api/PlanService";

interface State {
    isPlanPanel: boolean,
    plan: Plan,
    fileNames: string[],
    panel_to_show: number,
    fileName: string,
    bankAdd: {},
    isChanged: boolean
}

export class PlanLayout extends PureComponent<PlanLayoutProps, State> {
  constructor(props) {
    super(props);
    this.state= {
        isPlanPanel: true,
        plan: this.props.plan,
        fileNames: this.props.fileNames,
        panel_to_show: 0,
        fileName: "",
        bankAdd: {},
        isChanged: false
    }
    this.addChanneltoPlan = this.addChanneltoPlan.bind(this);
    this.updatePanelToShow = this.updatePanelToShow.bind(this);
    this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
    // this.getLastLoadedPlan = this.getLastLoadedPlan.bind(this);
    this.planSaved = this.planSaved.bind(this);
    this.planSavedAs = this.planSavedAs.bind(this);
    // this.getAllFileNames = this.getAllFileNames.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
    this.updateFileName = this.updateFileName.bind(this);
  }

  getPlanFromFileName(filename: string) {
    // gets called when filename is clicked on in load panel
    PlanService.getFileData(filename).then((response: any) => 
      response.json().then(data => {
        console.log("Getting Plan from Filename! ", data["details"]);
        this.setState({plan: data["details"]})
        this.setState({
          fileName: filename,
          panel_to_show: 0
        });
      }))
  }

  planSaved(fileName, plan) {
    /* Save File and Set fileName to state */
    const data = {
      name: fileName,
      details: plan,
      user: "admin"
    }
    console.log("Plan Saved! ", data)
    PlanService.saveFile(data).then((response: any) => 
      response.json().then(data => {
        //TODO: Need to refresh plan
        this.setState({
          fileName: fileName,
          panel_to_show: 0
        })
      })
    );
  }

  planSavedAs(plan) {
    const data = {
      name: plan.plan_filename,
      details: plan,
      user: "admin",
      is_deleted: 0,
      is_running: 0,
      updated_name: plan.plan_filename
    }
    PlanService.saveFileAs(data).then((response: any) => 
      response.json().then(data => {
        console.log("Plan Saved As! ", data);
      })
    )
  }
  
  deleteFile(fileName) {
    PlanService.deleteFile(fileName).then((response: any) => 
    response.json().then(data => {
      console.log("Plan Deleted! ", data)
      //TODO: need to refresh plan file names
    })
  );
  }

  addChanneltoPlan(bankx: number, channelx: number) {
    this.setState({
      bankAdd: {
        bank: bankx,
        channel: channelx
      }
    });
  }

  updatePanelToShow(panel: number) {
    this.setState({panel_to_show: panel})
  }

  updateFileName(x: boolean) {
    this.setState({ isChanged: x });
  }

  componentDidMount() {
    //get the last plan that was loaded
    // this.getLastLoadedPlan();
  }

  render() {
    const bankPanelsEdit = [];
    if (("bank" in this.props.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.props.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanelsEdit.push(
            <div key={i}>
              <BankPanel
                plan={this.state.plan}
                bank={i}
                key={i}
                uistatus={this.props.uistatus}
                ws_sender={this.props.ws_sender}
                addChanneltoPlan={this.addChanneltoPlan}
              />
            </div>
          );
        }
      }
    }

    let left_panel;
    switch (this.state.panel_to_show) {
      case PlanPanelTypes.PLAN:
        this.setState({isPlanPanel: true})
        left_panel = (
            <PlanPanel
                uistatus={this.props.uistatus}
                plan={this.state.plan}
                ws_sender={this.props.ws_sender}
                bankAddition={this.state.bankAdd}
                updateFileName={this.updateFileName}
                fileName={this.state.fileName}
                isChanged={this.state.isChanged}
                updatePanel={this.updatePanelToShow}
                layoutSwitch={this.props.layoutSwitch}
                planSavedAs={this.planSavedAs}
                // getLastLoadedPlan={this.getLastLoadedPlan}
            />
        );
        break;
      case PlanPanelTypes.LOAD:
        this.setState({isPlanPanel: false})
        left_panel = (
          <LoadPanel
            plan={this.state.plan}
            updateFileName={this.updateFileName}
            isChanged={this.state.isChanged}
            ws_sender={this.props.ws_sender}
            getPlanFromFileName={this.getPlanFromFileName}
            updatePanel={this.updatePanelToShow}
            fileNames={this.props.fileNames}
            deleteFile={this.deleteFile}
          />
        );
        break;
      case PlanPanelTypes.SAVE:
        this.setState({isPlanPanel: false})
        left_panel = (
            <SavePanel
                plan={this.state.plan}
                updateFileName={this.updateFileName}
                isChanged={this.state.isChanged}
                ws_sender={this.props.ws_sender}
                planSaved={this.planSaved}
                updatePanel={this.updatePanelToShow}
                fileNames={this.props.fileNames}
                deleteFile={this.deleteFile}
            />
        );
        break;
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
                  {bankPanelsEdit}
                </div>
              {this.state.isPlanPanel ? (
                <div className="ref-div">
                  <button
                    type="button"
                    id="reference"
                    onClick={e => {
                      // this.ws_sender({ element: "reference" })
                      this.addChanneltoPlan(0, 0);
                    }}
                    className={"btn btn-large ref-btn"}
                    style={{ color: "black" }}
                  >
                    Reference
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default PlanLayout
