import React, { Component  } from 'react';
import {EditorSingleInstrumentControls} from "./EditorSingleInstrumentControls";
import {
  PanelOptionsGroup,
   Select
 } from '@grafana/ui';

export class EditorIntrumentsControls extends Component<any, any>   {
  constructor(props) {
    super(props);
    this.state = {
      slotsCount: 0,
      "activeInstrumentIP": null,
    };
  }

  handleChange(field, e) {
    this.setState({"activeInstrumentIP": e.value["ip"]});
  }

  render() {
    const options = [];
    for (let i = 0; i < this.props.allInstrumentsData.length; i++) {
       options.push({'value': this.props.allInstrumentsData[i], 'label': this.props.allInstrumentsData[i]["displayName"]});
    }

    let controlComponent = <div />;
    let activeInstrument = null;
    if (this.state.activeInstrumentIP) {
      for (let i = 0; i < this.props.allInstrumentsData.length; i++) {
        if (this.props.allInstrumentsData[i]["ip"] === this.state.activeInstrumentIP) {
          activeInstrument = this.props.allInstrumentsData[i];
        }
      }
      controlComponent = <div className="InstrumentControls">
            <EditorSingleInstrumentControls
            activeInstrument={activeInstrument}
            parent={this}
            editorMode={true}
            />
            </div>;
    }
    return (
      <div>
        <PanelOptionsGroup title="Controls">

          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
              <span className="gf-form-label width-10">
                Instrument
              </span>
              <Select
                placeholder="---"
                options={options}
                key={"InstumentList"}
                onChange={this.handleChange.bind(this, "")}
              />
            </div>
          </div>
          {controlComponent}
        </PanelOptionsGroup>
      </div>
    );
  }
}
