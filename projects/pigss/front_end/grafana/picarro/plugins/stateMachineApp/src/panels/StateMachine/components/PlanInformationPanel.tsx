import React, { Component } from 'react'
import { Plan } from './../types'

interface State {
    
}

interface Props {
    uistatus: {
        [key: string]: any;
    },
    plan: Plan
}

export class PlanInformationPanel extends Component<Props, State> {
    constructor(props) {
        super(props)

    }

    getBankChannelFromStep(step: number) {
        // const stepInfo = this.props.plan.steps[String(step)]
        // let currentStepString;
        // if (stepInfo.reference != 0) {
        //     currentStepString = 'Reference'
        // }
        // for (let bank in stepInfo.banks) {

        // }

        // return currentStepString;
    }

    render() {
        const currentStep = this.props.plan.current_step;
        const currentDuration = this.props.plan.steps[String(this.props.plan.current_step)].duration;
        const currentPort = this.getBankChannelFromStep(currentStep);
        let nextStep = 0;
        if (currentStep == this.props.plan.last_step) {
            nextStep = 1;
        } else {
            nextStep = this.props.plan.last_step + 1;
        }
        const nextPort = this.getBankChannelFromStep(nextStep);
        return (
            <div>
                <div className="plan-info">
                    Running Plan: {this.props.plan.plan_filename} Current Port: {currentStep}
                    Duration: {currentDuration} Next Port: {nextStep}
                </div>
            </div>
        )};

}
