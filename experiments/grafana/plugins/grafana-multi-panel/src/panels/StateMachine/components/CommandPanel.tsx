import React, {Component, PureComponent} from 'react';
import {CommandPanelOptions} from './../types';

class CommandPanel extends PureComponent<CommandPanelOptions> {
    classNameOpt = { DISABLED:"btn-inverse disabled command-disabled", READY: "btn-outline-success", ACTIVE:"btn-success" }

    getDisabled = (element: string): boolean => {
        let disabled = true;
        const status_dict = (this.props.uistatus as any);
        if (element in status_dict) {
            disabled = (status_dict[element] === "DISABLED");
        }
        return disabled;
    }

    getClassNameOpt = (element: string): string => {
        let classNames = "";
        const status_dict = (this.props.uistatus as any);
        if (element in status_dict) {
            classNames = (this.classNameOpt as any)[status_dict[element]];
        }
        return classNames;
    }

    render() {
        return (
            <div className="panel-command" >
                <div style={{width: "100%", marginTop: 60}}>
                    <div className="grid-command" style={{display: "grid", gridTemplateColumns: "1fr 1fr", gridGap: 20, padding: 20 }}>
                        <button
                            onClick={e => this.props.ws_sender({element: "standby"})}
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
                            onClick={e => this.props.ws_sender({element: "run"})}
                            disabled = {this.getDisabled("run")}
                            value="run"
                            className={"btn btn-large btn-command " + this.getClassNameOpt("run")} >
                            Run
                        </button>
                        <button
                            onClick={e => this.props.ws_sender({element: "plan"})}
                            disabled = {this.getDisabled("plan")}
                            value="plan"
                            className={"btn btn-large btn-command " + this.getClassNameOpt("plan")} >
                            Edit Plan
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
