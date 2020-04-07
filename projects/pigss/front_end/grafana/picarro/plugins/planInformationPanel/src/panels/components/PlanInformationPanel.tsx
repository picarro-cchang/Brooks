import React, { Component } from "react";
import { Plan } from "./../types";

interface State {
  uistatus: { [key: string]: string };
  plan: Plan;
  timer: number;
}

interface Props {
  uistatus: {
    [key: string]: string;
  };
  plan: Plan;
  timer: number;
}

export class PlanInformationPanel extends Component<Props, State> {
  constructor(props) {
    super(props);

    this.state = {
      uistatus: this.props.uistatus,
      plan: this.props.plan,
      timer: this.props.timer
    };

  }

  getBankChannelFromStep(step: number, nextStep: number) {
    const stepInfo = this.props.plan.steps[String(step)];
    const nextStepInfo = this.props.plan.steps[String(nextStep)];
    let currentStepString, nextStepString;
    if (stepInfo.reference != 0) {
      currentStepString = "Reference";
    } else {
      for (const bank in stepInfo.banks) {
        if (stepInfo.banks.hasOwnProperty(bank)) {
          const bank_name = this.props.plan.bank_names[bank].name;
          const bank_config = stepInfo.banks[bank];
          if (bank_config.clean != 0) {
            currentStepString = `Clean ${bank_name}`;
            break;
          } else if (bank_config.chan_mask != 0) {
            const mask = bank_config.chan_mask;
            // Find index of first set bit using bit-twiddling hack
            const channel = (mask & -mask).toString(2).length;
            const ch_name = this.props.plan.bank_names[bank].channels[channel];
            const bankNum = Number(bank);
            const portNumber = (bankNum - 1) * 8 + channel;
            currentStepString = portNumber + ": " + ch_name;
            break;
          }
        }
      }
    }
    if (nextStepInfo.reference != 0) {
      nextStepString = "Reference";
    } else {
      for (const bank in nextStepInfo.banks) {
        if (nextStepInfo.banks.hasOwnProperty(bank)) {
          const bank_name = this.props.plan.bank_names[bank].name;
          const bank_config = nextStepInfo.banks[bank];
          if (bank_config.clean != 0) {
            nextStepString = `Clean ${bank_name}`;
            break;
          } else if (bank_config.chan_mask != 0) {
            const mask = bank_config.chan_mask;
            // Find index of first set bit using bit-twiddling hack
            const channel = (mask & -mask).toString(2).length;
            const ch_name = this.props.plan.bank_names[bank].channels[channel];
            const bankNum = Number(bank);
            const portNumber = (bankNum - 1) * 8 + channel;
            nextStepString = portNumber + ": " + ch_name;
            break;
          }
        }
      }
    }

    return { currentStepString, nextStepString };
  }

  planFileNameUpTop() {
    if (
      this.props.uistatus.plan_loop == "ACTIVE" ||
      this.props.uistatus.plan_run == "ACTIVE"
    ) {
      return true;
    } else {
      return false;
    }
  }

  render() {
    if (this.props.plan.last_step !== 0) {
      const currentStep = this.props.plan.current_step;
      const currentDuration = this.props.plan.steps[
        String(this.props.plan.current_step)
      ].duration;
      console.log('hello')
      let nextStep = 0;
      if (currentStep == this.props.plan.last_step) {
        nextStep = 1;
      } else {
        nextStep = this.props.plan.current_step + 1;
      }
      const steps = this.getBankChannelFromStep(currentStep, nextStep);
      const fileNameUpTop = this.planFileNameUpTop();
      return (
        <div style={{ textAlign: "center" }}>
          {fileNameUpTop ? (
            <div className="plan-info">
              Running Plan: {this.props.plan.plan_filename} Current Port: {steps.currentStepString}
              Duration: {currentDuration} Next Port: {steps.nextStepString}
            </div>
          ) : (
            <div className="plan-info">Running Plan: No Plan Running</div>
          )}
        </div>
      );
    } else {
      return (
        <div style={{ textAlign: "center" }} className="plan-info">
          No Plan Loaded
        </div>
      );
    }
  }
}
