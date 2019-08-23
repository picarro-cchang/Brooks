import React, {Component, PureComponent} from 'react';
import {OptionsPanelOptions} from './../types';
import deepmerge from "deepmerge";

class OptionsPanel extends PureComponent<OptionsPanelOptions> {
   // classNameOpt = { DISABLED:"btn-inverse disabled command-disabled", READY: "btn-outline-success", ACTIVE:"btn-success" }

    render() {
        return (
          <div className="panel-edit" style={{width: "100%"}}>
              <div>
                  <div className="grid-command" style={{ marginLeft: "70%" }} >
                      <button
                          value="edit"
                          className={"btn btn-large btn-command btn-danger"}
                          onClick={ (e) =>
                              this.props.ws_sender({element: "edit"})
                          }
                          style={{ borderRadius: 5, color: 'white', height: 40, width: 100, marginRight: 20}}>
                          Edit
                      </button>
                  </div>
              </div>
          </div>
        );
    }
}

export default OptionsPanel;
