import React, { Component } from "react";
import { Plan } from "./../types";
import "./planInformation.css";
import {Row, Col} from 'react-bootstrap'


interface State {
  uistatus: { [key: string]: any };
  plan: Plan;
  timeRemaining: number;
  timeStart: number;
  runType: Number;
}

export interface Props {
  uistatus: {
    [key: string]: any;
  };
  plan: Plan;
  timer: number;
  runType: Number;
}

export class PlanInformationPanel extends Component<Props, State> {
  constructor(props) {
    super(props);

    this.state = {
      uistatus: this.props.uistatus,
      plan: this.props.plan,
      timeStart: this.props.timer,
      timeRemaining: this.props.timer,
      runType: this.props.runType
    };
  }

  getBankChannelFromStep(step: number, nextStep: number) {
    const stepInfo = this.props.plan.steps[String(step)];
    const nextStepInfo = this.props.plan.steps[String(nextStep)];
    let currentStepString, nextStepString;
    if (stepInfo !== undefined){  if (stepInfo.reference != 0) {
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
      }}
    if (nextStepInfo !== undefined){if (nextStepInfo.reference != 0) {
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
      }}

    return { currentStepString, nextStepString };
  }

  // planFileNameUpTop() {
  //   if (
  //     this.props.uistatus.plan_loop == "ACTIVE" ||
  //     this.props.uistatus.plan_run == "ACTIVE"
  //   ) {
  //     return true;
  //   } else {
  //     return false;
  //   }
  // }

  render() {
      const currentStep = this.props.plan.current_step;
      let nextStep = 0;
      if (currentStep == this.props.plan.last_step) {
        nextStep = 1;
      } else {
        nextStep = this.props.plan.current_step + 1;
      }
      const steps = this.getBankChannelFromStep(currentStep, nextStep);
      let planName = this.props.plan.plan_filename
      if (this.props.plan.plan_filename == "") {
        planName = "No Plan Loaded"
      }
      return (
        <div className="width">
            <Row>
            <Col className={this.props.runType === 2 ? "info-row col-sm-4": "info-row col-sm-6"}>
              {this.props.runType === 0 ? (
                <div className={"col text-center br"} id="plan">
                <span className="titles">Plan Loaded: </span>
                <span className={"values"}>
                  {planName}{" "}
                </span>
              </div>
              ) : (
                <div className={"col text-center br"} id="plan">
                <span className="titles">Plan Running: </span>
                
                  {this.props.runType === 1 ? (
                  <span className={"values"}>
                    Single Port
                  </span>
                  ) : (
                  <span className={"values"}>
                    {planName}{" "}
                  </span>
                  )}
                  
              </div>
              )}
              
              </Col>
              <Col className={this.props.runType === 2 ? "text-center center-info info-row col-sm-4" : "ext-center center-info info-row col-sm-6"}>
                <div id="curr-port-line" className="row text-center">
                  <div id="curr-port" className="titles text-left">Measuring Port: </div>
                  <div id="curr-port" className="values text-left">{steps.currentStepString} </div>
                </div>
                {this.props.runType === 2 ? (
                  <div id="curr-port-time" className="row text-center">
                  <div id="curr-port" className="titles text-left"> Remaining Time: </div>
                  <div id="curr-port" className="values text-left">{this.props.timer} seconds</div>
                </div>
                ) : (null)}
              </Col>
              {this.props.runType === 2 ? (
                <Col sm={4} className={"text-center center-info-2 info-row"} id="next-port">
                <span className="titles">Next Port: </span>
                <span className="values"> {steps.nextStepString} </span>
              </Col>
              ) : (null)}
            </Row>
        </div>
      );
  }
}
