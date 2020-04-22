import React, { PureComponent } from "react";
import BankPanel from "./BankPanel";
import CommandPanel from "./CommandPanel";
import PlanLoadPanel from "./PlanLoadPanel";
import PlanPreview from "./PlanPreview";
import { PanelTypes, RunLayoutProps, Plan } from "../types";
import EditPanel from "./EditPanel";
import { PlanService } from "../../api/PlanService";
import Modal from 'react-responsive-modal';

interface State {
    plan: Plan, 
    fileNames: string[],
    panel_to_show: number,
    loadedPlanFilename: string,
    modal_info: {
      show: boolean,
      html: string,
      num_buttons: number, 
      buttons: {},
      action: string
    }
}

export class RunLayout extends PureComponent<RunLayoutProps, State> {
  constructor(props) {
    super(props);
    this.state = {
      plan: this.props.plan,
      fileNames: this.props.fileNames,
      panel_to_show: 0,
      loadedPlanFilename: "",
      modal_info: {
        show: false,
        html: "",
        num_buttons: 0,
        buttons: {},
        action: ""
      }
    }
    this.updatePanelToShow = this.updatePanelToShow.bind(this);
    // this.loadPlan = this.loadPlan.bind(this);
    this.cancelLoadPlan = this.cancelLoadPlan.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
    this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
    this.setModalInfo = this.setModalInfo.bind(this);
  }
  setModalInfo(show: boolean, html: string, num_buttons: number, buttons: {}, action) {
    console.log("Setting Modal for ", action)
    const modal = {
      show: show, 
      html: html,
      num_buttons: num_buttons,
      buttons: buttons,
      action: action
    }
    this.setState({modal_info: modal})
  }

  getPlanFromFileName(filename: string) {
    PlanService.getFileData(filename).then((response: any) => 
      response.json().then(data => {
        console.log(`Getting Plan from Filename ${filename}! `, data["details"]);
        if (data["message"]) {
          this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
        }  else {
        this.setState({plan: data["details"]})
        this.setState({
          loadedPlanFilename: filename,
          panel_to_show: 3
        });
      }
      }))
  }

  deleteFile(fileName) {
    PlanService.deleteFile(fileName).then((response: any) => 
    response.json().then(data => {
      console.log("Plan Deleted! ", data)
      if (data["message"]) {
        this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
      } 
      //TODO: need to refresh plan file names
    })
  );
  }

  async fileIsRunning(plan: Plan) {
    console.log("New Plan ", plan)
    const newPlan = {
      name: plan.plan_filename,
      details: plan,
      user: 'admin',
      is_running: 1,
      is_unloading: 1
    }
    PlanService.getLastRunning().then((response: any) => 
      response.json().then(data => {
        if (data["message"]) {
          console.log("No Plan I suppsoe")
          PlanService.overwriteFile(newPlan).then(response => 
            response.json().then(dat => {
              console.log(dat)
              if (dat["message"]) {
                // this.setModalInfo(true, `<h4 style='color: black'>${dat["message"]}</h4>`, 0, {}, 'misc')
              } 
            }))
      }          
      else {
        console.log("Plan ", { ...(JSON.parse(data['details'])) })
        const lastPlan = {
          name: data['name'],
          details:  { ...(JSON.parse(data['details'])) },
          user: 'admin',
          is_running: 0,
          is_unloading: 1
        }
        PlanService.overwriteFile(lastPlan).then(response => 
          response.json().then(data => {
            console.log("Last Plan ", data);
            PlanService.overwriteFile(newPlan).then(response => 
              response.json().then(plan => {
                console.log(plan)
                if (data["message"]) {
                  // this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
                } 
              }))
          }))
      }
    }))
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

  getLastRunningPlan() {
    PlanService.getLastRunning().then((response: any) => 
      response.json().then(data => {
        if (data["message"]) {
          console.log("No Plan I suppsoe")
        }          
        else {
          const plan = { ...(JSON.parse(data['details'])) }
          console.log("Last Running Plan Run ", plan)
          this.setState({plan: plan});
        }

      }))
  }

  async componentDidMount() {
    await this.getLastRunningPlan();
  }

  render() {
    console.log("Plan on Run Layout ", this.state.plan)
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
            setModalInfo={this.setModalInfo}
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
            setModalInfo={this.setModalInfo}
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
    const modalButtons = [];
    for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
      const modal_info = this.state.modal_info;
      const response = modal_info.buttons[i].response
      if (modal_info.action == "loadPlan") {
        if (response != null) {
        modalButtons.push(
          <button
            className={modal_info.buttons[i].className}
            style={{ margin: "10px" }}
            onClick={() => {
              this.updatePanelToShow(0)
              // this.props.currentStepChange(response.plan);
              this.props.ws_sender({
                element: "load_modal_ok",
                plan: response.plan
              })
              
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
              console.log("Canceling Load")
              this.props.ws_sender({
                element: "load_modal_cancel",
              })
              this.setModalInfo(false, "", 0, {}, "")
            }}
          >
            {modal_info.buttons[i].caption}
          </button>
        );
      }
    } else {
      if (response != null) {
        if (response.step != null) {
          response.plan.current_step = response.step
          modalButtons.push(
            <button
              className={modal_info.buttons[i].className}
              style={{ margin: "10px" }}
              onClick={() => {
                this.updatePanelToShow(0)
                this.fileIsRunning(response.plan);
                //TODO: Send Plan Info to BackEnd 
                this.props.ws_sender({
                  element: "modal_step_1",
                  plan: response.plan
                })
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
                this.updatePanelToShow(0)
                this.fileIsRunning(response.plan);
                //TODO: Send Plan Info to BackEnd 
                this.props.ws_sender({
                  element: "modal_ok",
                  plan: response.plan
                })
                this.setModalInfo(false, "", 0, {}, "")
              }}
            >
              {modal_info.buttons[i].caption}
            </button>
          );
        }
      } else {
        modalButtons.push(
          <button
            className={modal_info.buttons[i].className}
            style={{ margin: "10px" }}
            onClick={() => {
              this.props.ws_sender({element: "modal_close"})
              this.setModalInfo(false, "", 0, {}, "")
            }}
          >
            {modal_info.buttons[i].caption}
          </button>
        );
      }
    }}

    return (
      <div style={{ textAlign: "center" }}>
        <h1>Plan Loaded: {this.state.plan.plan_filename}</h1>
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
export default RunLayout
