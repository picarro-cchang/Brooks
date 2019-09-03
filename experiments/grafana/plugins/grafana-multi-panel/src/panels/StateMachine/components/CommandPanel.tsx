import React, {Component, PureComponent} from 'react';
import {CommandPanelOptions} from './../types';
import {element} from "prop-types";

class CommandPanel extends PureComponent<CommandPanelOptions> {
    run_plan = this.props.uistatus["run"];
   // manual = this.props.uistatus["run"];
    loop_plan = this.props.uistatus["run"];

    classNameOpt = { DISABLED:"btn-inverse disabled command-disabled", READY: "btn-outline-success", ACTIVE:"btn-success " };
   runclassNameOpt = { DISABLED:"btn-inverse disabled command-disabled", READY: "btn-outline-success", ACTIVE:"btn-success disabled" };
    editplanOpt = {ACTIVE: "btn-outline-success", READY: "btn-outline-success", DISABLED:"btn-inverse disabled command-disabled btn-run-issue"};

    getDisabled = (element: string): boolean => {
        let disabled = true;
        const status_dict = (this.props.uistatus as any);
        if (element in status_dict) {
            disabled = (status_dict[element] === "DISABLED");
        }
        return disabled;
    }

    getClassNameOpt = (element: string, specific?: string): string => {
        let classNames = "";
        const status_dict = (this.props.uistatus as any);
        if (element in status_dict) {
            if (element === "plan") {
                classNames = (this.editplanOpt as any)[status_dict[element]];

            }
            else if (element === "manual_run" || element === "loop_plan" || element === "run_plan") {
                classNames = (this.runclassNameOpt as any)[status_dict[element]];
            }
            else {
                classNames = (this.classNameOpt as any)[status_dict[element]];
            }
        }

        return classNames;
    };

    // getrunClassNameOpt = (element: string): string => {
    //     let classNames = "";
    //     // if (element === "manual") {
    //     //     const status = this.manual;
    //     //     console.log("manual ", status);
    //     //     classNames = (this.runclassNameOpt as any)[status]
    //     // }
    //     // else
    //     if (element === "run_plan") {
    //         const status = this.run_plan;
    //         classNames = (this.runclassNameOpt as any)[status]
    //     }
    //     else {
    //         const status = this.loop_plan;
    //         classNames = (this.runclassNameOpt as any)[status]
    //     }
    //     return classNames;
    // };



    render() {

        return (
            <div className="panel-command" >
                <div style={{width: "100%", marginTop: 20}}>
                    <div className="grid-command" style={{display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gridGap: 5, padding: 20 }}>
                        <button
                            onClick={(e) =>{
                                this.props.ws_sender({element: "standby"});
                                this.run_plan = "READY";
                                this.loop_plan = "READY";
                                //this.manual = "READY";
                            }}
                            disabled = {this.getDisabled("standby")}
                            value="standby"
                            className={"btn btn-large btn-command btn-1-3 " + this.getClassNameOpt("standby")}>
                            Standby
                        </button>
                        <button
                            onClick={e => this.props.ws_sender({element: "identify"})}
                            disabled = {this.getDisabled("identify")}
                            value="identify"
                            className={"btn btn-large btn-command btn-1-3 " + this.getClassNameOpt("identify")} >
                            Identify Available Channels
                        </button>
                        <button
                            onClick={e => this.props.ws_sender({element: "plan"})}
                            disabled = {this.getDisabled("plan")}
                            value="plan"
                            className={"btn btn-large btn-command btn-1-3 "+ this.getClassNameOpt("plan")} >
                            Edit Plan
                        </button>
                        <button
                            onClick={(e) =>{
                                this.props.ws_sender({element: "run"});
                                // ##set run plan & loop to disabled
                                // // this.manual = "ACTIVE";
                                // this.run_plan = "DISABLED";
                                // this.loop_plan = "DISABLED";
                              //  console.log("manual ", this.props.uistatus["manual"]);

                            }}
                            disabled = {this.getDisabled("manual_run")}
                            value="run"
                            className={"btn btn-large btn-command btn-run " + this.getClassNameOpt("manual_run")} >
                            Run Channel
                        </button>
                        <button
                            onClick={(e) => {
                                this.props.ws_sender({element: "plan_run"})

                            }}
                            disabled = {this.getDisabled("run_plan")}
                            value="run_plan"
                            className={"btn btn-large btn-command btn-run " + this.getClassNameOpt("run_plan")}>
                            Run Plan
                        </button>
                        <button
                            onClick={(e) => {
                                this.props.ws_sender({element: "plan_loop1"});
                            }}
                            disabled = {this.getDisabled("loop_plan")}
                            className={"btn btn-large btn-command btn-run " + this.getClassNameOpt("loop_plan")}>
                            Loop Plan
                        </button>
                        <button
                            onClick={e => this.props.ws_sender({element: "reference"})}
                            disabled = {this.getDisabled("reference")}
                            value="reference"
                            className={"btn btn-large btn-command btn-1-3 " + this.getClassNameOpt("reference")}>
                            Reference
                        </button>
                        <button
                            value="edit"
                            className={"btn btn-large btn-edit btn-danger"}
                            onClick={ (e) =>
                                this.props.ws_sender({element: "edit"})
                            }>
                            Edit Labels
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}

export default CommandPanel;
