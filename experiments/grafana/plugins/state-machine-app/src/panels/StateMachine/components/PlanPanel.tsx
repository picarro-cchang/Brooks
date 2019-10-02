import React, {Component, PureComponent, ReactText} from 'react';
import ReactList from 'react-list';
import {Plan, PlanFocus, PlanPanelOptions, PlanStep} from './../types';

class PlanPanel extends PureComponent<PlanPanelOptions> {
    state = {
        refVisible: true,
        isChanged: false
    };


    focusComponent:any = null;
    focusTimer:any = null;

    manageFocus = (component: any) => {
        // Manages focus by storing the component which is to receive focus
        //  and calling its focus() method after a short timeout. Multiple
        //  calls to manageFocus during the expiry of the timer will cause
        //  only the last component to receive the focus. This prevents
        //  oscillations in which a cycle of components receive focus in
        //  quick succession.
       // console.log("Manage Focus", component);
        if (this.focusTimer !== null) {
            clearTimeout(this.focusTimer);
        }
        this.focusComponent = component;
        this.focusTimer = setTimeout(() => {
          //  console.log("Setting focus", this.focusComponent)
            this.focusComponent.focus();
            this.focusTimer = null;
        }, 200);
    };

    makePlanRow = (row: number) => {
        let portString = "";
        let durationString = "";
        if (this.props.plan.last_step >= row) {
            const planRow = this.props.plan.steps[row] as PlanStep;
            if (planRow.reference != 0) {
                portString = "Reference";
            }
            else {
                for (let bank in planRow.banks) {
                    if (planRow.banks.hasOwnProperty(bank)) {
                        const bank_name = this.props.plan.bank_names[bank].name;
                        const bank_config = planRow.banks[bank];
                        if (bank_config.clean != 0) {
                            portString = `Clean ${bank_name}`;
                            break;
                        }
                        else if (bank_config.chan_mask != 0) {
                            const mask = bank_config.chan_mask;
                            // Find index of first set bit using bit-twiddling hack
                            const channel = (mask & (-mask)).toString(2).length;     
                            const ch_name = this.props.plan.bank_names[bank].channels[channel];
                            portString = bank_name + ", " + ch_name;
                            break;
                        }
                    }
                }
            }
            if (planRow.duration !== 0) {
                durationString = `${planRow.duration}`;
            }
        }
        return (
            <div className="gf-form-inline" key={row}>
                <label className="col-sm-1" style={{color: "black", marginRight: "-5px"}}>{row}</label>
                <div className="col-sm-6 col-bank-name">
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 1) && this.manageFocus(input)}
                           type="text" className="form-control plan-input" id={"plan-port-" + row}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:1}})
                           }}
                           onChange={(e) => this.setState({isChanged: true})}
                           style={{ backgroundColor: 'white', maxWidth: "100%", float: "left"}}
                           value={portString} placeholder="Select port"/>
                </div>
                <div className="col-sm-3" style={{paddingLeft: "0px", paddingRight: "5px"}}>
                    <input ref={input => input && (this.props.plan.focus.row === row) &&
                        (this.props.plan.focus.column === 2) && this.manageFocus(input)}
                           onChange={(e) => {
                               this.props.ws_sender({element: "plan_panel", row, duration: e.target.value});
                               this.setState({isChanged: true})
                           }}
                           onFocus={(e) => {
                               this.props.ws_sender({element: "plan_panel", focus:{row, column:2}})
                           }}
                           maxLength={8}
                           minLength={1}
                           type="text" className="form-control input-small plan-input" id={"plan-duration-" + row}
                           style = {{ maxWidth: "100%"}}
                           value={durationString} placeholder="Duration" />
                </div>
                <label style={{color: "black", marginLeft: "-15px", paddingRight: "5px"}}>s</label>
                <label className="col-sm-1 radio-btn">
                    <input type="radio" id={"plan-row-" + row} checked={row == this.props.plan.current_step}
                     onChange={e => this.props.ws_sender({element: "plan_panel", current_step: row})}
                     style={{maxWidth: "100%"}}
                    />
                    <span className="checkmark"></span>
                </label>
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
        // console.log(this.props.plan.plan_filename);
        const file_name = this.props.plan.plan_filename;
        return (
            <div>
            <div className="panel-plan" >
                <h2 style={{color: "#5f5f5f"}}>Schedule</h2>
                <h6 style={{color: "black"}}>Please click on available channels to set up a schedule,
                    then click on the radio button to select starting position.</h6>
               {(this.props.plan.plan_filename && !this.state.isChanged)?
                   <h6 style={{color: "black"}}>Currently viewing File: {file_name}</h6> : <h6 style={{color: "black"}}>Currently not viewing a saved file</h6>
               }
                <div className="panel-plan-inner" >
                    <form>
                        <ReactList
                            itemRenderer={this.renderItem}
                            length={this.props.plan.max_steps}
                            type={"uniform"}
                        />
                    </form>
                </div>
                <div className="container">
                    <div className="row text-center btn-row-1" >
                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => {
                                        this.props.ws_sender({element: "plan_insert"});
                                        this.setState({isChanged: true});
                                    }}
                                    className={"btn btn-block btn-group"}
                                    style={{backgroundImage: "-webkit-linear-gradient(top, rgb(77, 78, 78), rgb(8, 8, 8)"}}>
                                Insert
                            </button>
                        </div>
                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_save"})}
                                    className={"btn btn-block btn-light btn-group"}
                                    style={{backgroundImage: "-webkit-linear-gradient(top, rgb(77, 78, 78), rgb(8, 8, 8)"}}>
                                Save
                            </button>
                        </div>


                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    onClick={e => this.props.ws_sender({element: "plan_load"})}
                                    className={"btn btn-block btn-light btn-group"}
                                    style={{backgroundImage: "-webkit-linear-gradient(top, rgb(77, 78, 78), rgb(8, 8, 8)"}}>
                            Load
                            </button>
                        </div>
                    </div>
                    <div className="row btn-row-2">
                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    disabled={this.props.plan.focus.row > this.props.plan.last_step}
                                    onClick={e => {
                                        this.props.ws_sender({element: "plan_delete"});
                                        this.setState({isChanged: true});
                                    }}
                                    className={"btn btn-block btn-danger btn-group"}>
                                Delete
                            </button>
                        </div>

                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    onClick={e => {
                                        this.props.ws_sender({element: "plan_ok"})
                                    }}
                                    className={"btn btn-block btn-success btn-group"}>
                                OK
                            </button>
                        </div>
                        <div className="col-sm-3" style={{paddingRight: "5px", paddingLeft: "5px"}}>
                            <button type="button"
                                    onClick={e => {
                                        this.props.ws_sender({element: "plan_cancel"});
                                    }}
                                    className={"btn btn-block btn-danger btn-group"} >
                                Cancel
                            </button>
                        </div>
                    </div>


                </div>
            </div>

            </div>
        );
    }
}

export default PlanPanel;
