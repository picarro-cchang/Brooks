import { any } from "prop-types";

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

export interface BankConfig {
  chan_mask: number;
  clean: number;
}

export interface PlanStep {
  banks: { [key: number]: BankConfig };
  reference: number;
  duration: number;
}
