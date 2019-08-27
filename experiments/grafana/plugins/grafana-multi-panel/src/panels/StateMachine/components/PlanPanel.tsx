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
                const bank_name = this.props.plan.bank_names[this.props.plan.steps[row].bank].name;
                const ch_name = this.props.plan.bank_names[this.props.plan.steps[row].bank].channels[this.props.plan.steps[row].channel];
                // portString = `Bank ${planRow.bank}, Channel ${planRow.channel}`;
                portString = bank_name + ", " + ch_name;
            }
            if (planRow.duration !== 0) {
                durationString = `${planRow.duration}`;
            }
        }
        return (
            <div className="gf-form-inline" key={row}>
                <label className="col-sm-1" style={{color: "black", marginRight: -20}}>{row}</label>
                <div className="col-sm-6">
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 1) && this.manageFocus(input)}
                           type="text" className="form-control input-medium" id={"plan-port-" + row}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:1}})
                           }}
                           style={{ backgroundColor: 'white', border: "1px solid black", borderRadius: 2, marginRight: -20, color: 'black'}}
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
                           style={{ backgroundColor: 'white', border: "1px solid black", borderRadius: 2, marginBottom: 5, color: 'black'}}

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
            <div className="panel-plan" style={{ height: 675, backgroundColor: "#888", padding: 10, border: "3px solid #111", borderRadius: 7 }}>
                <h2 style={{color: "white"}}>Schedule</h2>
                <h6>Please click on available channels to select port.</h6>
                <div style={{overflowX: "hidden", overflowY: "auto", maxHeight:440, borderRadius: 3}}>
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.max_steps}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="container" style={{width: "90%"}}>
                    <div className="row text-center" style={{marginTop: "10px"}}>
                        <div className="col-sm-6">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_insert"})}
                                    className={"btn btn-block btn-secondary"} style={{ width: 110, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Insert
                            </button>
                        </div>
                        <div className="col-sm-6">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_delete"})}
                                    className={"btn btn-block btn-danger"} style={{ width: 110, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Delete
                            </button>
                        </div>
                    </div>
                    <div className="row text-center" style={{marginTop: "10px"}}>
                        <div className="col-sm-6">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_load"})}
                                    className={"btn btn-block btn-inverse"} style={{ width: 110, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Load
                            </button>
                        </div>
                        <div className="col-sm-6">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_save"})}
                                    className={"btn btn-block btn-inverse"} style={{ width: 110, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Save
                            </button>
                        </div>
                    </div>
                    <div className="row text-center" style={{marginTop: "10px", marginBottom: "10px", marginLeft: -25}}>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_cancel"})}
                                    className={"btn btn-block btn-danger"}  style={{ marginBottom: 10,  width: 95, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Cancel
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_loop"})}
                                    className={"btn btn-block btn-success"} style={{ marginBottom: 10,  width: 95, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
                                Loop
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_ok"})}
                                    className={"btn btn-block btn-success"} style={{ marginBottom: 10,  width: 95, height: 40, borderRadius: 5, textAlign: "center", fontSize: 20}}>
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
