import React, {Component} from "react"


import {
  picarroLogo,
  teledyneLogo,
  blackMesaLogo,
  cheeseMasterLogo
    } from '../types';

var logos = {
            "picarro_logo":picarroLogo,
            "teledyne_logo":teledyneLogo,
            "black_mesa_logo":blackMesaLogo,
            "cheese_master_logo":cheeseMasterLogo}

function isColor(strColor){
  // console.log(strColor)
  var s=new Option().style;
  s.color = strColor;
  // console.log(s.color)

  return s.color == strColor;
}


export class InstrumentSmalViewComponent extends Component<any, any> {
  constructor(props) {
    super(props)
    this.state = {
     // "instrument":this.props.instrument,
     "parent": this.props.parent,
     // "ip":this.props.instrument['ip']
    }
    this.setThisActive = this.setThisActive.bind(this)
  }
  setThisActive(ip){
    this.state.parent.setActive(ip)
  }

  render(){

    var isActive = this.props.activeInstrument == this.props.instrument['ip']
    const img =  <img height="20" src={logos[this.props.instrument['logo_path']]} />

    var statusColor = "grey"
    if (isColor(this.props.instrument["status_color"])){statusColor=this.props.instrument["status_color"]}
    // console.log(this.props.instrument["ip"])
    return(
      <div 
        className={isActive ?  'active-instrument':"inactive-instrument" }
        style={{width:150}}>
      <div
        
          style={{borderColor: isActive ?  'red':undefined }}
          onClick={() => {this.setThisActive(this.props.instrument['ip'])} } 
          className="card-item"
          >
            <figure className="card-item-figure">{img}</figure>
            <div className="card-item-details">
            <div className="input-color">
                <div 
                  className="color-box" 
                  style={{backgroundColor:statusColor}}></div>
            </div>
              <h4> {this.props.instrument["displayName"]}</h4>
              <div className="card-item-name">IP: {this.props.instrument["ip"]}</div>
              <div className="card-item-name">Status: {this.props.instrument["status"]}</div>

              {typeof(this.props.instrument["warnings"]) != "undefined" && this.props.instrument["warnings"]!="" && 
                <p>&#9888;</p>}
            </div>
            </div>
      </div>
    )
  }
}

// export default InstrumentSmalViewComponent
              // {this.props.instrument["Model"]!="" && 
              //     <div class="card-item-sub-name">Model: {this.props.instrument["Model"]}</div>}

              // {this.props.instrument["Serial Number"]!="" && 
              //   <div class="card-item-sub-name">Serial Number: {this.props.instrument["Serial Number"]}</div>}