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
    },
    loadedFileName: string;
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
      },
      loadedFileName: this.props.loadedFileName
    }
    this.updatePanelToShow = this.updatePanelToShow.bind(this);
    this.cancelLoadPlan = this.cancelLoadPlan.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
    this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
    this.setModalInfo = this.setModalInfo.bind(this);
  }

  shouldComponentUpdate(nextProps) {
    if (this.props.loadedFileName !== nextProps.loadedFileName) {
      console.log("New FileName ", nextProps.loadedFileName, " Old File")
      this.setState({
        loadedFileName: nextProps.loadedFileName
      });
    } else if (this.props.fileNames !== nextProps.fileNames) {
      console.log("New List of FileNames ", nextProps.fileNames)
      this.setState({fileNames: nextProps.fileNames})
    } else if (this.props.plan.current_step !== nextProps.plan.current_step && nextProps.plan.current_step !== null) {
      const plan = {...this.state.plan}
      plan.current_step = nextProps.plan.current_step
      console.log("New Step ", nextProps.plan.current_step)
      this.setState({plan})
    }
    return true;
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
      if (data["message"]) {
        this.setModalInfo(true, `<h4 style='color: black'>${data["message"]}</h4>`, 0, {}, 'misc')
        this.props.getPlanFileNames();
        this.forceUpdate();
      } 
      else {
        console.log("Plan Deleted! ", data)
        this.props.getPlanFileNames();
      }
    })
  );
  }

  updatePanelToShow(panel: number) {
    this.setState({panel_to_show: panel})
  } 

  cancelLoadPlan(){
    //set old state?
    //disabled run and loop
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

  render() {
    // console.log("Plan on Run Layout ", this.state.plan)
    // console.log("Plan on Main ", this.props.plan)
    // console.log("STEP ON RUN ", this.state.plan.current_step)
    // console.log("STEP ON MAIN ", this.props.plan.current_step)
    let left_panel;
    switch (this.state.panel_to_show) {
      case PanelTypes.NONE:
        left_panel = (
          <CommandPanel
            plan={this.props.plan}
            uistatus={this.props.uistatus}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
            layoutSwitch={this.props.layoutSwitch}
            setModalInfo={this.setModalInfo}
            loadedFileName={this.state.loadedFileName}
          />
        );
        break;
      case PanelTypes.LOAD:
        left_panel = (
          <PlanLoadPanel
            plan={this.props.plan}
            ws_sender={this.props.ws_sender}
            updatePanel={this.updatePanelToShow}
            fileNames={this.props.fileNames}
            cancelLoadPlan={this.cancelLoadPlan}
            deleteFile={this.deleteFile}
            getPlanFromFileName={this.getPlanFromFileName}
            loadedFileName={this.state.loadedFileName}
          />
        );
        break;
      case PanelTypes.EDIT:
        left_panel = (
          <EditPanel
            plan={this.props.plan}
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
            fileNames={this.state.fileNames}
            cancelLoadPlan={this.cancelLoadPlan}
            setModalInfo={this.setModalInfo}
            loadedFileName={this.state.loadedFileName}
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
                plan={this.props.plan}
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

    const modalButtons = []
    switch (this.state.modal_info.action) {
      case "loadPlan":
        for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
          const modal_info = this.state.modal_info;
          const response = modal_info.buttons[i].response
          if (response != null) {
            modalButtons.push(
              <button
                className={modal_info.buttons[i].className}
                style={{ margin: "10px" }}
                onClick={() => {
                  this.updatePanelToShow(0);
                  this.props.ws_sender({
                    element: "load_modal_ok",
                    name: response.name,
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
        }
        break;
        case "loopPlan":
          // console.log("STATE STEP ON HERE ", this.state.plan.current_step)
          for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
            const modal_info = this.state.modal_info;
            const response = modal_info.buttons[i].response
            if (response != null) {
              if (response.step != null) {
                response.plan.current_step = response.step
                modalButtons.push(
                  <button
                    className={modal_info.buttons[i].className}
                    style={{ margin: "10px" }}
                    onClick={() => {
                      this.updatePanelToShow(0);
                      this.props.ws_sender({
                        element: "modal_step_1"
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
                      this.props.ws_sender({
                        element: "modal_ok"
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
        }
        break;
        case "runPlan":
          // console.log("STATE STEP ON HERE ", this.state.plan.current_step)
          for (let i = 1; i <= this.state.modal_info.num_buttons; i++) {
            const modal_info = this.state.modal_info;
            const response = modal_info.buttons[i].response
            if (response != null) {
              if (response.step != null) {
                response.plan.current_step = response.step
                modalButtons.push(
                  <button
                    className={modal_info.buttons[i].className}
                    style={{ margin: "10px" }}
                    onClick={() => {
                      this.updatePanelToShow(0);
                      this.props.ws_sender({
                        element: "modal_step_1"
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
                      this.props.ws_sender({
                        element: "modal_ok"
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
              this.props.ws_sender({element: "modal_close"})
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
        {/* <h1>Plan Step: {this.state.plan.current_step}</h1> */}
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
            this.props.ws_sender({ element: "modal_close" })
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
