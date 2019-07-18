import React, {Component, PureComponent} from 'react';
import { stat } from 'fs';
import { ENGINE_METHOD_NONE } from 'constants';

interface PlanStep {
    bank: number;
    channel: number;
    duration: number;
}

interface PlanFocus {
    row: number;
    column: number;
}

interface Plan {
    show: boolean,
    focus: PlanFocus,
    last_step: number,
    steps: { [key: string]: PlanStep }
}

interface PlanPanelOptions {
    uistatus: { [key: string]: string; }
    plan: Plan;
    setFocus: (row: number, column: number) => void;
    ws_sender: (o: object) => void;
}


class PlanPanel extends PureComponent<PlanPanelOptions> {
    focusComponent:any = null;
    focusTimer:any = null;

    manageFocus = (component: any) => {
        // Manages focus by storing the component which is to receive focus
        //  and calling its focus() method after a short timeout. Multiple
        //  calls to manageFocus during the expiry of the timer will cause
        //  only the last component to receive the focus. This prevents 
        //  oscillations in which a cycle of components receive focus in 
        //  quick succession. 
        console.log("Manage Focus", component);
        if (this.focusTimer !== null) {
            clearTimeout(this.focusTimer);
        }
        this.focusComponent = component;
        this.focusTimer = setTimeout(() => {
            console.log("Setting focus", this.focusComponent)
            this.focusComponent.focus();
            this.focusTimer = null;
        }, 200);
    }

    makePlanRow = (row: number) => {
        let portString = "";
        let durationString = "";
        if (this.props.plan.last_step >= row) {
            const planRow = this.props.plan.steps[row];
            if (planRow.bank !== 0) {
                portString = `Bank ${planRow.bank}, Channel ${planRow.channel}`;
            }
            if (planRow.duration !== 0) {
                durationString = `${planRow.duration}`;
            }
        }
        return (
            <div className="form-row" key={row}>
                <label className="col-sm-1  small-input">{row}</label>
                <div className="col-sm-7">
                    <input ref={input => input && (this.props.plan.focus.row === row) && 
                                (this.props.plan.focus.column === 1) && this.manageFocus(input)} 
                     type="text" className="form-control small-input" id={"plan-port-" + row} 
                     onFocus={(e) => {
                            this.props.ws_sender({element: "plan_panel", focus:{row, column:1}})
                    }}
                    value={portString} placeholder="Select port"  readOnly/>
                </div>
                <div className="col-sm-4">
                    <input ref={input => input && (this.props.plan.focus.row === row) && 
                                (this.props.plan.focus.column === 2) && this.manageFocus(input)} 
                     onChange={(e) => this.props.ws_sender({element: "plan_panel", row, duration: e.target.value})}
                     onFocus={(e) => {
                        this.props.ws_sender({element: "plan_panel", focus:{row, column:2}})
                     }}
                     type="text" className="form-control small-input" id={"plan-duration-" + row} 
                     value={durationString} placeholder="Duration" />
                </div>
            </div>
        );
    }

    render() {
        let planRows = [];
        for (let row=1; row<=20; row++) {
            planRows.push(this.makePlanRow(row));
        }
        return (
            <div className="panel-plan" >
                <h2>Schedule</h2>
                <form style={{marginBottom: "10px"}}>
                    {planRows}
                </form>
                <div className="container">
                    <div className="row text-center">
                        <div className="col-sm-2">
                            <button type="button"
                                disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                onClick={e => this.props.ws_sender({element: "plan_insert"})}
                                className={"btn btn-sm btn-info"}>
                                Insert
                            </button>
                        </div>
                        <div className="col-sm-2">
                            <button type="button"
                                disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                onClick={e => this.props.ws_sender({element: "plan_delete"})}
                                className={"btn btn-sm btn-danger"}>
                                Delete
                            </button>
                        </div>
                        <div className="col-sm-2">
                            <button type="button"
                                onClick={e => this.props.ws_sender({element: "plan_load"})}
                                className={"btn btn-sm btn-dark"}>
                                Load
                            </button>
                        </div>
                        <div className="col-sm-2">
                            <button type="button"
                                onClick={e => this.props.ws_sender({element: "plan_save"})}
                                className={"btn btn-sm btn-dark"}>
                                Save
                            </button>
                        </div>
                        <div className="col-sm-2">
                            <button type="button"
                                onClick={e => this.props.ws_sender({element: "plan_loop"})}
                                className={"btn btn-sm btn-success"}>
                                Loop
                            </button>
                        </div>
                        <div className="col-sm-2">
                            <button type="button"
                                onClick={e => this.props.ws_sender({element: "plan_ok"})}
                                className={"btn btn-sm btn-success"}>
                                OK
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default PlanPanel;
