// export interface Options {
//   imageUrl: string;
//   updateInterval: number;
// }
//
// export const defaults: Options = {
//   imageUrl: "",
//   updateInterval: 60 * 5
// };

// export const defaults: CommandPanelOptions = {
//
// }

export interface ButtonInfo {
  caption: string;
  className: string;
  response: string;
}

export interface CommandPanelOptions {
  uistatus: {
    [key: string]: string;
  }
  ws_sender: (o: object)=>void;
  plan: Plan;
  refVisible: boolean;
  onEditClick: () => void;
}

export interface ModalInfo {
  show: boolean,
  html: string,
  num_buttons: number,
  buttons: { [key: string]: ButtonInfo }
}

export interface Plan {
  max_steps: number,
  panel_to_show: number,
  current_step: number,
  focus: PlanFocus,
  last_step: number,
  steps: { [key: string]: PlanStep }
  num_plan_files: number,
  plan_files: { [key: string]: string },
  plan_filename: string,
  bank_names: {
    [key: number]: {
      name: string,
      channels: { [key: number]: string }
    }
  }
}

export interface PlanFocus {
  row: number;
  column: number;
}

export interface PlanLoadPanelOptions {
  plan: Plan;
  ws_sender: (o: object) => void;
}

export interface PlanPanelOptions {
  uistatus: { [key: string]: string; }
  plan: Plan;
  setFocus: (row: number, column: number) => void;
  ws_sender: (o: object) => void;
  refVisible: boolean;
  onCancelOkClick: () => void;
}

export enum PlanPanelTypes {
  NONE = 0,
  PLAN = 1,
  LOAD = 2,
  SAVE = 3,
  EDIT = 4,
}

export interface PlanSavePanelOptions {
  plan: Plan;
  ws_sender: (o: object) => void;
}

export interface PlanStep {
  bank: number;
  channel: number;
  duration: number;
}

export interface Options {
  panel_to_show: number;
}

export enum OptionsPanelTypes {
  NONE = 0,
  EDIT = 1,
}

export interface EditPanelOptions {
  uistatus: {
    [key: string]: string;
  }
  ws_sender: (o: object)=>void;
  //switches: (v: any) => void;
  plan: Plan
}
