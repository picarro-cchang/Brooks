import React, { Component } from 'react'

import {EditorSingleInstrumentControls} from "./EditorSingleInstrumentControls"

export class InstrumentViewComponent extends Component<any, any> {
  constructor(props) {
    super(props)
    this.state = {"parent":this.props.parent}
  }

  render(){
    var instrument = this.props.activeInstrument

    if (instrument == null){
      var placeholder = <h1>NO ACTIVE INSTRUMENT</h1>
    } else {
      var placeholder = <div className="InstrumentControls">
              <EditorSingleInstrumentControls 
              activeInstrument={this.props.activeInstrument}
              parent={this}
              editorMode={true}
              />
              </div>
    }
    return(
      <div>
        {placeholder}
      </div>)
  }
}

export default InstrumentViewComponent