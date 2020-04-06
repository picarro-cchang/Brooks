import React, { Component } from 'react';
import {PlanInformationPanel} from './PlanInformationPanel';
import { Plan } from '../types';

interface State {
    uistatus: { [key: string]: any},
    plan: Plan
}
export class PlanInformationPanelLayout extends Component<any, any> {
    constructor(props) {
        super(props)

    }

    //get uistatus & plan

    render() {
        return (
            <div>
                <PlanInformationPanel 
                    uistatus={this.state.uistatus}
                    plan={this.state.plan}
                />
            </div>
        )
    }
}
