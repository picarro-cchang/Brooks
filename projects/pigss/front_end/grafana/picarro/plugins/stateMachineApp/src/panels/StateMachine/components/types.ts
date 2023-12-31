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

export interface PlanLayoutProps {
    uistatus: {
      [key: string]: any;
    };
    // ws_sender: (o: object) => void;
    plan: Plan;
    layoutSwitch: () => void;
    fileNames: {}
    getPlanFileNames: () => void;
    loadedFileName: string;
}

export interface RunLayoutProps {
    uistatus: {
      [key: string]: any;
    };
    ws_sender: (o: object) => void;
    plan: Plan;
    layoutSwitch: () => void;
    fileNames: {}
    loadedFileName: string;
    getPlanFileNames: () => void;
    runPaneltoShow: number
}

export enum PanelTypes {
    NONE = 0,
    LOAD = 1,
    EDIT = 2,
    PREVIEW = 3
}

export enum PlanPanelTypes {
    PLAN = 0,
    LOAD = 1,
    SAVE = 2,
}

export interface BankPanelPlanOptions {
    bank: number;
    uistatus: {
      bank?: { [bankNum: string]: string };
      clean?: { [bankNum: string]: string };
      channel?: { [bankNum: string]: { [channelNum: string]: string } };
    };
    plan: Plan;
    addChanneltoPlan: (bank: number, channel: number) => void;
}

export interface LoadPanelCommandOptions {
    plan: Plan;
    ws_sender: (o: object) => void;
    fileNames: {}
    getPlanFromFileName: (fileName: string) => void;
    deleteFile: (file: string, id: number) => void;
    loadedFileName: string;
    planID: String;
  }

  export interface PreviewPanelOptions {
    plan: Plan;
    ws_sender: (o: object) => void;
    fileNames: {}
    loadedFileName: string;
    planID: String;
  }


  export interface LoadPanelOptions {
    plan: Plan;
    isEdited: boolean;
    updateFileName: (x: boolean) => void;
    updatePanel: (x: number) => void;
    fileNames: {}
    getPlanFromFileName: (fileName: string) => void;
    deleteFile: (file: string, id: number) => void;
    loadedFileName: string;
  }

export interface PlanPanelOptions {
    uistatus: { [key: string]: any };
    plan: Plan;
    isEdited: boolean;
    updateFileName: (x: boolean) => void;
    bankAddition: { [key: string]: number };
    fileName: string;
    updatePanel: (x: number) => void;
    layoutSwitch: () => void;
    planOverwrite: (s: object, x: String) => void;
    setModalInfo: (s: boolean, h: string, n: number, b: object, a: string) => void;
    updateSavedFileState: (plan: Plan) => void;
    planID: String;
  }

  export interface PlanSavePanelOptions {
    plan: Plan;
    isEdited: boolean;
    updateFileName: (x: boolean) => void;
    planSaved: (f: string, d: object) => void;
    updatePanel: (x: number) => void;
    fileNames: {}
    deleteFile: (file: string, id: number) => void;
    setModalInfo: (s: boolean, h: string, n: number, b: object, a: string) => void;
  }

  export interface ButtonInfo {
    caption: string;
    className: string;
    response: string;
  }
  

  export interface ModalInfo {
    show: boolean;
    html: string;
    num_buttons: number;
    buttons: { [key: string]: ButtonInfo };
  }

  export interface EditPanelOptions {
    uistatus: {
      [key: string]: any;
    };
    ws_sender: (o: object) => void;
    plan: Plan;
    planID: String;
  }

  export interface CommandPanelOptions {
    uistatus: {
      [key: string]: string;
    };
    ws_sender: (o: object) => void;
    plan: Plan;
    layoutSwitch: () => void;
    loadedFileName: string;
    planID: String;
  }
