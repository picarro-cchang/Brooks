import { any } from "prop-types";

export interface ButtonInfo {
  caption: string;
  className: string;
  response: string;
}

export interface CommandPanelOptions {
  uistatus: {
    [key: string]: string;
  };
  ws_sender: (o: object) => void;
  plan: Plan;
}

export interface ModalInfo {
  show: boolean;
  html: string;
  num_buttons: number;
  buttons: { [key: string]: ButtonInfo };
}

export interface Plan {
  max_steps: number;
  panel_to_show: number;
  current_step: number;
  focus: PlanFocus;
  last_step: number;
  steps: { [key: string]: PlanStep };
  num_plan_files: number;
  plan_files: { [key: string]: string };
  plan_filename: string;
  bank_names: {
    [key: number]: {
      name: string;
      channels: { [key: number]: string };
    };
  };
}

export interface PlanFocus {
  row: number;
  column: number;
}

export interface PlanLoadPanelOptions {
  plan: Plan;
  ws_sender: (o: object) => void;
  isChanged: boolean;
  updateFileName: (x: boolean) => void;
}

export interface PlanPanelOptions {
  uistatus: { [key: string]: string };
  plan: Plan;
  setFocus: (row: number, column: number) => void;
  ws_sender: (o: object) => void;
  isChanged: boolean;
  updateFileName: (x: boolean) => void;
  // addChanneltoPlan: (bank: number, channel: number) => void;
  bankAddition: {[key: string]: number}
}

export enum PlanPanelTypes {
  NONE = 0,
  PLAN = 1,
  LOAD = 2,
  SAVE = 3,
  EDIT = 4
}

export interface PlanSavePanelOptions {
  plan: Plan;
  ws_sender: (o: object) => void;
  isChanged: boolean;
  updateFileName: (x: boolean) => void;
}

export interface BankConfig {
  chan_mask: number;
  clean: number;
}

export interface PlanStep {
  banks: { [key: number]: BankConfig };
  reference: number;
  duration: number;
}

export interface EditPanelOptions {
  uistatus: {
    [key: string]: any;
  };
  ws_sender: (o: object) => void;
  plan: Plan;
}
