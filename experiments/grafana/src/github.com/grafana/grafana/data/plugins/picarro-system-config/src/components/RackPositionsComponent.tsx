import React, {Component} from "react"
import {InstrumentSmalViewComponent} from "./InstrumentSmalViewComponent"

export class RackPositionsComponent extends Component<any, any> {
  constructor(props) {
    super(props)

    this.state = {
      "parent":this.props.parent,
      "slots_n":this.props.slots_n
    }
  }

  setActive(ip){this.state.parent.setActive(ip)}

  render(){
    var positions = new Array(this.state.slots_n).fill(null)

    for (var i = 0; i < this.props.instrumentsWithPosition.length; i++) {
       positions[this.props.instrumentsWithPosition[i]["position_in_rack"]-1] = this.props.instrumentsWithPosition[i]
    }

    var items = []
    for (var i = 1; i <= this.state.slots_n; i++) {
      items.push(<RackSingelPositionComponent 
                  key={i} 
                  position={i} 
                  instrument={positions[i-1]} 
                  parent={this} 
                  activeInstrument={this.props.activeInstrument}/>
      )
    }

    return(
      <div style={{width:185}}>
        <div className="panel-header">
          <div className="panel-title-container" panel-ctrl="ctrl">
            <span className="panel-title">
              <span className="panel-title-text">KNOWNN INSTRUMENTS</span>
            </span>
          </div>
        </div>
        <div style={{width:175}}>
          {items}
        </div>
      </div>
      )
   }
}

class RackSingelPositionComponent extends Component<any, any> {
   constructor(props) {
      super(props)
      this.state = {
         "parent":this.props.parent,
      }
      this.setActive = this.setActive.bind(this)
   }

   setActive(ip){this.state.parent.setActive(ip)}

   render(){
      var state = {
         "position":this.props.position,
         "instrument":this.props.instrument}

      if (state.instrument != null) {
         var placeholder = <div>
            <InstrumentSmalViewComponent 
               key={state.instrument["Serial Number"]} 
               instrument={state.instrument}
               parent={this}
               activeInstrument={this.props.activeInstrument}/>
            </div>
         } else {
         var placeholder = <span>Unoccupied Space</span> 
         }

      return(
         <div 
         className="dashlist-link dashlist-link-dash-db" >
            <h4> Position {state.position}</h4>
            {placeholder}
         </div>
      )
   }
}
