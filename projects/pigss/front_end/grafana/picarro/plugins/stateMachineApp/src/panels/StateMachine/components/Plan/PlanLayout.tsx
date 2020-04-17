import React, { PureComponent } from "react";
import BankPanel from "./BankPanel";
import LoadPanel from "./LoadPanel";
import PlanPanel from "./PlanPanel";
import SavePanel from "./SavePanel";
import deepmerge from "deepmerge";
import { PlanLayoutProps, Plan, PlanPanelTypes } from "../types";
import { PlanService } from "../../api/PlanService";
import Modal from 'react-responsive-modal';

interface State {
    isPlanPanel: boolean,
    plan: Plan,
    fileNames: string[],
    panel_to_show: number,
    fileName: string,
    bankAdd: {},
    isChanged: boolean
    modal_info: {
      show: boolean,
      html: string,
      num_buttons: number, 
      buttons: {},
      action: string
    }
}
export const storageKey = 'planStorage';

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
        isChanged: false,
        modal_info: {
          show: false,
          html: "",
          num_buttons: 0,
          buttons: {},
          action: ""
        }
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
    this.setModalInfo = this.setModalInfo.bind(this);
  }

  setModalInfo(show: boolean, html: string, num_buttons: number, buttons: {}, action) {
    const modal = {
      show: show, 
      html: html,
      num_buttons: num_buttons,
      buttons: buttons,
      action: action
    }
    this.setState({modal_info: modal})
  }
  
  getPlanStorage = () => {
    // get picarroStorage object from sessionStorage
    if (window.sessionStorage) {
      return sessionStorage.getItem(storageKey);
    }
    return null;
  }

  setPlanStorage = (planStorage: Plan) => {
    // set picarroStorage object in sessionStorage
    if (window.sessionStorage) {
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(planStorage));
      } catch (error) {
        this.clearPlanStorage();
      }
    }
  }

  clearPlanStorage = () => {
    sessionStorage.removeItem(storageKey);
  }

  getStateFromSavedData = () => {
    const savedData = this.getPlanStorage();
    if (savedData !== null) {
      return { ...(JSON.parse(savedData)) };
    }
    return null;
  }

  isSavedDataCurrent = (planState: Plan) => {
    // if (planState !== null && planState.last_step !== 0) {
    //   return planState.steps.length ? n : false;
    // }
    // return false;
  }

  getPlanFromFileName(filename: string) {
    PlanService.getFileData(filename).then((response: any) => 
      response.json().then(data => {
        console.log(`Getting Plan from Filename ${filename}! `, data["details"]);
        this.setPlanStorage(data["details"]);
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
    const storedPlan = this.getStateFromSavedData();
    if(this.state.plan != storedPlan){
      this.setState({
        plan: storedPlan,
        fileName: storedPlan.plan_filename
      })
    }
  }

  componentWillUnmount() {
    console.log("saving storage")
    this.setPlanStorage(this.state.plan)
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
                setPlanStorage={this.setPlanStorage}
                getStateFromSavedData={this.getStateFromSavedData}
                setModalInfo={this.setModalInfo}
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
                getStateFromSavedData={this.getStateFromSavedData}
                setModalInfo={this.setModalInfo}
            />
        );
        break;
    }

    const modalButtons = [];
    for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
      const modal_info = this.state.modal_info;
      if (modal_info.action == "save") {
        const response = modal_info.buttons[i].response
        console.log("filename" ,response)
        if (response != null) {
          modalButtons.push(
            <button
              className={modal_info.buttons[i].className}
              style={{ margin: "10px" }}
              onClick={() => {
                this.planSaved(response.filename, response.plan)
                this.setModalInfo(false, "", 0, {}, "")
              }}
            >
              {modal_info.buttons[i].caption}
            </button>
          );
        } else {
          modalButtons.push(
            <button
              className={modal_info.buttons[i].className}
              style={{ margin: "10px" }}
              onClick={() => {
                this.setModalInfo(false, "", 0, {}, "")
              }}
            >
              {modal_info.buttons[i].caption}
            </button>
          );
        }
      } else if (modal_info.action == "saveOverwrite") {
        const response = modal_info.buttons[i].response
        console.log("filename" ,response)
        if (response != null ) {
          modalButtons.push(
            <button
              className={modal_info.buttons[i].className}
              style={{ margin: "10px" }}
              onClick={() => {
                this.planSavedAs(response.plan)
                this.setModalInfo(false, "", 0, {}, "")
              }}
            >
              {modal_info.buttons[i].caption}
            </button>
          );
        } else {
          modalButtons.push(
            <button
              className={modal_info.buttons[i].className}
              style={{ margin: "10px" }}
              onClick={() => {
                this.setModalInfo(false, "", 0, {}, "")
              }}
            >
              {modal_info.buttons[i].caption}
            </button>
          );
        }
      } else if (modal_info.action == "validation") {
        modalButtons.push(
          <button
            className={modal_info.buttons[i].className}
            style={{ margin: "10px" }}
            onClick={() => {
              // this.planSaved(info[0], info[1])
              this.setModalInfo(false, "", 0, {}, "")
            }}
          >
            {modal_info.buttons[i].caption}
          </button>
        );

      } else {
        modalButtons.push(
          <button
            className={modal_info.buttons[i].className}
            style={{ margin: "10px" }}
            onClick={() => {
              // this.planSaved(info[0], info[1])
              this.setModalInfo(false, "", 0, {}, "")
            }}
          >
            {modal_info.buttons[i].caption}
          </button>
        );
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

        <Modal
          styles={{ overlay: { color: "black" } }}
          open={this.state.modal_info.show}
          onClose={() => {
            this.setModalInfo(false, "", 0, {}, "")
            // this.ws_sender({ element: "modal_close" })
          }}
          center
        >
          <div style={{ margin: "20px" }}>
            <div
              dangerouslySetInnerHTML={{ __html: this.state.modal_info.html }}
            ></div>
          </div>
          {modalButtons}
        </Modal>
      </div>
    );
  }
}

export default PlanLayout
