import React, {Component, PureComponent} from 'react';
import { stat } from 'fs';

interface CommandPanelOptions {
    uistatus: {
        [key: string]: string;
    }
}

class CommandPanel extends PureComponent<CommandPanelOptions> {
    classNameOpt = { DISABLED:"btn-outline-info", READY: "btn-outline-success", ACTIVE:"btn-success" }

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
            <div className="panel-command">
                <div style={{width: "100%"}}>
                    <div className="grid-command">
                        <button
                            disabled = {this.getDisabled("standby")}
                            value="standby"
                            className={"btn btn-lg btn-command btn-1-3 " + this.getClassNameOpt("standby")}>
                            Standby
                        </button>
                        <button
                            disabled = {this.getDisabled("identify")}
                            value="identify"
                            className={"btn btn-lg btn-command btn-1-3 " + this.getClassNameOpt("identify")}>
                            Identify
                        </button>
                        <button
                            disabled = {this.getDisabled("run")}
                            value="run"
                            className={"btn btn-lg btn-command " + this.getClassNameOpt("run")}>
                            Run
                        </button>
                        <button
                            disabled = {this.getDisabled("plan")}
                            value="plan"
                            className={"btn btn-lg btn-command " + this.getClassNameOpt("plan")}>
                            Plan
                        </button>
                        <button
                            disabled = {this.getDisabled("reference")}
                            value="reference"
                            className={"btn btn-lg btn-command btn-1-3 " + this.getClassNameOpt("reference")}>
                            Reference
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}

/*
    <button style={{fontSize: "0.9em"}}
        className="btn btn-info btn-lg btn-command btn-1-3">
        <div style={{textAlign: "left"}}>
            Testing<br/>
            div in button
        </div>
    </button>
*/
export default CommandPanel;