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
                           type="text" className="form-control plan-input" id={"plan-port-" + row}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:1}})
                           }}
                           style={{ backgroundColor: 'white'}}
                           value={portString} placeholder="Select port" readOnly/>
                </div>
                <div className="col-sm-4">
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 2) && this.manageFocus(input)}
                           onChange={(e) => this.props.ws_sender({element: "plan_panel", row, duration: e.target.value})}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:2}})
                           }}
                           type="text" className="form-control input-small plan-input" id={"plan-duration-" + row}
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
            <div className="panel-plan" >
                <h2 style={{color: "#5f5f5f"}}>Schedule</h2>
                <h6 style={{color: "#5f5f5f"}}>Please click on available channels to select port.</h6>
                <div className="panel-plan-inner" >
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.max_steps}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="container" style={{width: "90%"}}>
                    <div className="row text-center btn-row-1" >
                        <div className="col-sm-4">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_insert"})}
                                    className={"btn btn-block btn-secondary btn-group-1"} >
                                Insert
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => this.props.ws_sender({element: "plan_delete"})}
                                    className={"btn btn-block btn-danger btn-group-1"}>
                                Delete
                            </button>
                        </div>
                    </div>
                    <div className="row  btn-row-1">
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_load"})}
                                    className={"btn btn-block btn-inverse btn-group-1"} >
                                Load
                            </button>
                        </div>
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_save"})}
                                    className={"btn btn-block btn-inverse btn-group-1"} >
                                Save
                            </button>
                        </div>
                    </div>
                    <div className="row text-center btn-row-2" >
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_cancel"})}
                                    className={"btn btn-block btn-danger btn-group-2"} >
                                Cancel
                            </button>
                        </div>
                        {/*<div className="col-sm-4">*/}
                        {/*    <button type="button"*/}
                        {/*            onClick={e => this.props.ws_sender({element: "plan_loop"})}*/}
                        {/*            className={"btn btn-block btn-success btn-group-2"}>*/}
                        {/*        Loop*/}
                        {/*    </button>*/}
                        {/*</div>*/}
                        <div className="col-sm-4">
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_ok"})}
                                    className={"btn btn-block btn-success btn-group-2"}>
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
