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
    isEdited: boolean
    modal_info: {
      show: boolean,
      html: string,
      num_buttons: number, 
      buttons: {},
      action: string
    },
    loadedFileName: string,
}
export const storageKey = 'planStorage';

export class PlanLayout extends PureComponent<PlanLayoutProps, State> {
  constructor(props) {
    super(props);
    this.state= {
        isPlanPanel: true,
        plan: {
          max_steps: 32,
          panel_to_show: 0,
          current_step: 1,
          focus: { row: 1, column: 1 },
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
        },
        fileNames: this.props.fileNames,
        panel_to_show: 0,
        fileName: "",
        bankAdd: {},
        isEdited: false,
        modal_info: {
          show: false,
          html: "",
          num_buttons: 0,
          buttons: {},
          action: ""
        },
        loadedFileName: this.props.loadedFileName,
    }
    this.addChanneltoPlan = this.addChanneltoPlan.bind(this);
    this.updatePanelToShow = this.updatePanelToShow.bind(this);
    this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
    // this.getLastLoadedPlan = this.getLastLoadedPlan.bind(this);
    this.planSaved = this.planSaved.bind(this);
    this.planOverwrite = this.planOverwrite.bind(this);
    // this.getAllFileNames = this.getAllFileNames.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
    this.updateFileName = this.updateFileName.bind(this);
    this.setModalInfo = this.setModalInfo.bind(this);
    this.updateSavedFileState = this.updateSavedFileState.bind(this);
  }

  // shouldComponentUpdate(nextProps) {
  //   if (this.props.loadedFileName !== nextProps.loadedFileName) {
  //     console.log("New FileName ", nextProps.loadedFileName)
  //     this.setState({
  //       loadedFileName: nextProps.loadedFileName
  //     });
  //   }
  //   return true;
  // }

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

  getPlanFromFileName(filename: string) {
    PlanService.getFileData(filename).then((response: any) => 
      response.json().then(data => {
        if (data["message"]) {
          this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
        } else {
          console.log(`Getting Plan from Filename ${filename}! `, data["details"]);
          this.setPlanStorage(data["details"]);
          this.setState({plan: data["details"]}, () => console.log("Set it!!!! ", this.state.plan))
          this.setState({
            fileName: filename,
            panel_to_show: 0
          });
      }
      }))
  }

  updateSavedFileState(plan: Plan) {
    this.setState({plan: plan})
  }

  planSaved(fileName, plan) {
    // /* Save File and Set fileName to state */
    // const plan = {...this.state.plan}
    // plan.plan_filename = fileName
    // this.setState({plan}, () => 
    // console.log(this.state.plan.plan_filename)
    plan.plan_filename = fileName
    const data = {
      name: fileName,
      details: plan,
      user: "admin"
    }
    console.log("Plan Saved! ", data, "plan name ", plan.plan_filename)
    PlanService.saveFile(data).then((response: any) => 
      response.json().then(data => {
        //TODO: Need to refresh plan
        // if (data["message"]) {
          // this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
          this.props.getPlanFileNames();
        // } else {
        //   this.props.getPlanFileNames();
          this.getPlanFromFileName(fileName);
          this.setState({isEdited: false})
        // }
      })
    );
  }

  planOverwrite(plan) {
    const data = {
      name: plan.plan_filename,
      details: plan,
      user: "admin",
      is_deleted: 0,
      is_running: 0,
    }
    PlanService.overwriteFile(data).then((response: any) => 
      response.json().then(data => {
        console.log("Plan Saved As! ", data);
        // if (data["message"]) {
          console.log("HELLO", data["message"])
          // this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
          this.getPlanFromFileName(plan.plan_filename)
          this.setState({
            isEdited: false
          })
        // }
      })
    )
  }
  
  deleteFile(fileName) {
    PlanService.deleteFile(fileName).then((response: any) => 
    response.json().then(data => {
      if (data["message"]) {
        this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
        this.props.getPlanFileNames();
      } else {
        console.log("Plan Deleted! ", data)
        this.props.getPlanFileNames();
      }
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
    this.setState({ isEdited: x });
  }

  // componentDidMount() {
  //   const storedPlan = this.getStateFromSavedData();
  //   // if(this.state.plan != storedPlan && storedPlan != null){
  //   //   console.log("Doesn't match")
  //   //   this.setState({
  //   //     plan: storedPlan,
  //   //     fileName: storedPlan.plan_filename
  //   //   })
  //   // }
  // }

  // componentWillUnmount() {
  //   console.log("saving storage")
  //   this.setPlanStorage(this.state.plan)
  // }

  render() {
    const bankPanelsEdit = [];
    if (("bank" in this.props.uistatus) as any) {
      for (let i = 1; i <= 4; i++) {
        if ((this.props.uistatus as any).bank.hasOwnProperty(i)) {
          bankPanelsEdit.push(
            <div key={i}>
              <BankPanel
                plan={this.props.plan}
                bank={i}
                key={i}
                uistatus={this.props.uistatus}
                // ws_sender={this.props.ws_sender}
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
                // ws_sender={this.props.ws_sender}
                bankAddition={this.state.bankAdd}
                updateFileName={this.updateFileName}
                fileName={this.state.fileName}
                isEdited={this.state.isEdited}
                updatePanel={this.updatePanelToShow}
                layoutSwitch={this.props.layoutSwitch}
                planOverwrite={this.planOverwrite}
                setPlanStorage={this.setPlanStorage}
                getStateFromSavedData={this.getStateFromSavedData}
                setModalInfo={this.setModalInfo}
                updateSavedFileState={this.updateSavedFileState}
            />
        );
        break;
      case PlanPanelTypes.LOAD:
        this.setState({isPlanPanel: false})
        left_panel = (
          <LoadPanel
            plan={this.state.plan}
            updateFileName={this.updateFileName}
            isEdited={this.state.isEdited}
            // ws_sender={this.props.ws_sender}
            getPlanFromFileName={this.getPlanFromFileName}
            updatePanel={this.updatePanelToShow}
            fileNames={this.props.fileNames}
            deleteFile={this.deleteFile}
            loadedFileName={this.props.loadedFileName}
          />
        );
        break;
      case PlanPanelTypes.SAVE:
        this.setState({isPlanPanel: false})
        left_panel = (
            <SavePanel
                plan={this.state.plan}
                updateFileName={this.updateFileName}
                isEdited={this.state.isEdited}
                // ws_sender={this.props.ws_sender}
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

    const modalButtons = []
    switch (this.state.modal_info.action) {
      case "save":
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
          const response = modal_info.buttons[i].response
          if (response != null) {
            modalButtons.push(
              <button
                className={modal_info.buttons[i].className}
                style={{ margin: "10px" }}
                onClick={() => {
                  this.planSaved(response.filename, this.state.plan)
                  this.updateFileName(false)
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
        }
        break;
      case "saveOverwrite":
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
          const response = modal_info.buttons[i].response
          if (response != null ) {
            modalButtons.push(
              <button
                className={modal_info.buttons[i].className}
                style={{ margin: "10px" }}
                onClick={() => {
                  this.planOverwrite(response.plan)
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
        }
        break;
      case "validation":
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
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
        break;
      case 'exitPlan':
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
          const response = modal_info.buttons[i].response
          if (response != null ) {
            modalButtons.push(
              <button
                className={modal_info.buttons[i].className}
                style={{ margin: "10px" }}
                onClick={() => {
                  this.props.layoutSwitch();
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
        }
        break;
        
      default:
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
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
        break;
    }
    // for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
    //   const modal_info = this.state.modal_info;
    //   if (modal_info.action == "save") {
        
    //   } else if (modal_info.action == "saveOverwrite") {
        
        
    //   } else if (modal_info.action == "validation") {
        

    //   } else {
        
    //   }
    // }
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
