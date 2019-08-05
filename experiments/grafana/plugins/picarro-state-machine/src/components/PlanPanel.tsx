import React, {Component, PureComponent, ReactText} from 'react';
import ReactList from 'react-list';
import {Plan, PlanFocus, PlanPanelOptions, PlanStep} from './../types';

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
            <div className="gf-form-inline" key={row}>
                <label className="col-sm-1">{row}</label>
                <div className="col-sm-6">
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 1) && this.manageFocus(input)}
                           type="text" className="form-control input-medium" id={"plan-port-" + row}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:1}})
                           }}
                           style={{ backgroundColor: 'white', borderRadius: 3, marginRight: -20, color: 'black'}}
                           value={portString} placeholder="Select port"  readOnly/>
                </div>
                <div className="col-sm-4">
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 2) && this.manageFocus(input)}
                           onChange={(e) => this.props.ws_sender({element: "plan_panel", row, duration: e.target.value})}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:2}})
                           }}
                           type="text" className="form-control input-small" id={"plan-duration-" + row}
                           style={{ backgroundColor: 'white', borderRadius: 3, marginBottom: 5, color: 'black'}}

                           value={durationString} placeholder="Duration" />
                </div>
            </div>
        );
    }

    renderItem = (index: number, key: ReactText) => <div key={key}>{this.makePlanRow(index + 1)}</div>

    render() {
        /*
        let planRows = [];
        for (let row=1; row<=this.props.plan.max_steps; row++) {
            planRows.push(this.makePlanRow(row));
        }
        */
        return (
            <div className="panel-plan" style={{marginTop: 10, height: 550, backgroundColor: "#888", padding: 10, border: "3px solid #111", borderRadius: 10 }}>
                <h2>Schedule</h2>
                <div style={{overflowX: "hidden", overflowY: "auto", maxHeight:340}}>
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.max_steps}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="container">
                    <div className="row text-center" style={{marginTop: "10px"}}>
                        <div className="col-sm-6">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_insert"})}
                                    className={"btn btn-large btn-block btn-secondary"}>
                                Insert
                            </button>
                        </div>
                        <div className="col-sm-6">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_delete"})}
                                    className={"btn btn-large btn-block btn-danger"}>
                                Delete
                            </button>
                        </div>
                    </div>
                    <div className="row text-center" style={{marginTop: "10px"}}>
                        <div className="col-sm-6">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_load"})}
                                    className={"btn btn-large btn-block btn-inverse"}>
                                Load
                            </button>
                        </div>
                        <div className="col-sm-6">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_save"})}
                                    className={"btn btn-large btn-block btn-inverse"}>
                                Save
                            </button>
                        </div>
                    </div>
                    <div className="row text-center" style={{marginTop: "10px", marginBottom: "10px"}}>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_cancel"})}
                                    className={"btn btn-large btn-block btn-danger"}  style={{ marginBottom: 10}}>
                                Cancel
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_loop"})}
                                    className={"btn btn-large btn-block btn-success"} style={{ marginBottom: 10}}>
                                Loop
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_ok"})}
                                    className={"btn btn-large btn-block btn-success"} style={{ marginBottom: 10}}>
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
