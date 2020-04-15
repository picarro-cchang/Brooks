// import React, { PureComponent } from "react";
// import PlanPanel from "./PlanPanel";
// import PlanLoadEditPanel from "./PlanLoadEditPanel";
// import PlanSavePanel from "./PlanSavePanel"
// import { PlanPanelLayoutOptions, Plan } from "./types";
// import deepmerge from "deepmerge";
// import "react-toastify/dist/ReactToastify.css";
// import { threadId } from "worker_threads";

// interface State {
//   panel: string;
//   isLoaded: boolean;
//   fileName: string;
// }

// export class PlanPanelLayout extends PureComponent<
//   PlanPanelLayoutOptions,
//   State
// > {
//   constructor(props) {
//     super(props);
//     this.state = {
//       panel: "PLAN",
//       isLoaded: false,
//       fileName: ""
//     };
//     this.getPlanFromFileName = this.getPlanFromFileName.bind(this);
//     this.loadFile = this.loadFile.bind(this);
//     this.editPlan = this.editPlan.bind(this);
//     this.savePlan = this.savePlan.bind(this);
//     this.planSaved = this.planSaved.bind(this);
//   }

//   getPlanFromFileName(filename: string) {
//     // gets called when filename is clicked on in load panel
//     this.setState({
//       isLoaded: true,
//       fileName: filename,
//       panel: "PLAN"
//     });
//   }

//   loadFile() {
//     this.setState({ panel: "LOAD" });
//   }

//   editPlan() {
//     this.setState({ panel: "PLAN" });
//   }

//   savePlan() {
//     this.setState({ panel: "SAVE"});
//   }

//   planSaved(fileName) {
//     this.setState({
//       isLoaded: true,
//       fileName: fileName,
//       panel: "PLAN"
//     })
//   }

//   render() {
//     let left_panel;
//     switch (this.state.panel) {
//       case "PLAN":
//         left_panel = (
//           <PlanPanel
//             uistatus={this.props.uistatus}
//             plan={this.props.plan} // idk if i should use props or state, probably props
//             setFocus={(row, column) => this.props.setFocus(row, column)}
//             bankAddition={this.props.bankAddition}
//             updateFileName={this.props.updateFileName}
//             fileName={this.state.fileName}
//             isChanged={this.props.isChanged}
//             ws_sender={this.props.ws_sender}
//             loadFile={this.loadFile}
//             savePlan={this.savePlan}
//             updatePanel={this.props.updatePanel}
//           />
//         );
//         break;
//       case "SAVE":
//         left_panel = (
//           <PlanSavePanel
//             plan={this.props.plan}
//             updateFileName={this.props.updateFileName}
//             isChanged={this.props.isChanged}
//             ws_sender={this.props.ws_sender}
//             planSaved={this.planSaved}
//             editPlan={this.editPlan}
//             updatePanel={this.props.updatePanel}
//             fileNames={this.props.fileNames}
//           />
//         );
//         break;
//       case "LOAD":
//         left_panel = (
//           <PlanLoadEditPanel
//             plan={this.props.plan}
//             updateFileName={this.props.updateFileName}
//             isChanged={this.props.isChanged}
//             ws_sender={this.props.ws_sender}
//             getPlanFromFileName={this.getPlanFromFileName}
//             editPlan={this.editPlan}
//             updatePanel={this.props.updatePanel}
//             getPlanFileNames={this.props.getPlanFileNames}
//             fileNames={this.props.fileNames}
//           />
//         );
//         break;
//     }

//     return left_panel;
//   }
// }
// export default PlanPanelLayout;
