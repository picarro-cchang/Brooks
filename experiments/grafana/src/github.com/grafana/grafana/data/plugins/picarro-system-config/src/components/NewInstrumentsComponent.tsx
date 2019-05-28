import React, {Component} from "react"
import {InstrumentSmalViewComponent} from "./InstrumentSmalViewComponent"

export class NewInstrumentsComponent extends Component<any, any> {
   constructor(props) {
      super(props)
      this.state={
         "parent":this.props.parent
      }
   this.setActive = this.setActive.bind(this)

   }
   setActive(event){
      this.state.parent.setActive(event)
   }

   render(){
      var state = {
         "instrumentsData":this.props.instruments
      }
      const instrumentsWidgets = state.instrumentsData.map(instrument => 
            <InstrumentSmalViewComponent 
                  key={instrument["Serial Number"]} 
                  instrument={instrument}
                  parent={this}
                  activeInstrument={this.props.activeInstrument}/>
                  )

      return (

         <div>
        <div className="panel-header">


          <div className="panel-title-container" panel-ctrl="ctrl">
            <span className="panel-title">
              <span className="panel-title-text">NEW INSTRUMENTS</span>

            </span>
          </div>
        </div>
        {instrumentsWidgets}
      </div>
      )
   }
}

// export default NewInstrumentsComponent