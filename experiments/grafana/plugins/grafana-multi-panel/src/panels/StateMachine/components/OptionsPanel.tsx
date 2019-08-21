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
                          // onClick={e => this.props.ws_sender({element: "edit"})}
                          onClick={ (e) =>
                              this.props.switches(4)
                              // this.props.ws_sender({element: "edit"});
                              // console.log(this.state.options.panel_to_show);
                              // this.setState(deepmerge(this.state, { options: { panel_to_show: 4  } }));
                              // console.log(this.state.options.panel_to_show);

                          }
                          style={{ borderRadius: 5, color: 'white', height: 40, width: 100, marginRight: 20}}>
                          Edit
                      </button>
                      <button
                          value="override"
                          className={"btn btn-large btn-command btn-secondary"}
                          style={{ borderRadius: 5, color: 'white', height: 40, width: 100 }}>
                          Override
                      </button>
                  </div>
              </div>
          </div>
        );
    }
}

export default OptionsPanel;
