import React, {Component} from "react";
import PicarroAPI from "../api/PicarroAPI";
import {
  ISDestroyInstrument,
  ISRestartInstrument,
  ISResolveWarning,
  ISChangeDisplayName,
  logos
    } from '../types';

import {
  FormField,
  FormLabel,
  } from '@grafana/ui';

const FormFieldUnchangeable = (_a) => {
    const label = _a.label;
    const labelWidth = _a.labelWidth;
    const inputWidth = _a.inputWidth;
    const valueText = _a.valueText;
    return(
    <div className="form-field">
      <FormLabel width={labelWidth}> {label}</FormLabel>
      <div className={"gf-form-input width-" + inputWidth}
       >{valueText}</div>
    </div>);
};

export class EditorSingleInstrumentControls extends Component<any, any> {
   constructor(props) {
      super(props);

      this.handleChange = this.handleChange.bind(this);
      this.handleClick = this.handleClick.bind(this);
      this.state = {
        "parent": this.props.parent,
        "newDisplayName": "",
        "editorMode": this.props.editorMode
      };
   }

   handleChange(event) {
     this.setState({ "newDisplayName": event.target.value});

   }

   handleClick(event) {
      const {
        value,
        name
        } = event.target;

      if (name==="destroy-button") {
        PicarroAPI.postData(ISDestroyInstrument, {
             ip: value
          });
      }
      if (name==="restart-button") {
        PicarroAPI.postData(ISRestartInstrument, {
             ip: value
          });
      }

      if (name==="resolved-button") {
        const array = value.split('#@#');
        PicarroAPI.postData(ISResolveWarning, {
            ip: array[0],
            warning: array[1]
          });
      }
      if (name==="changeDisplayName-button") {
        const array = value.split(',');
        PicarroAPI.postData(ISChangeDisplayName, {
            ip: array[0],
            newDisplayName: array[1]
          });
      }
   }


   render() {
      const instrument = this.props.activeInstrument;
      let placeholder = <div />;
      if (instrument != null) {
        //Instrument logo
        const img =  <img height="40" src={logos[instrument['logo_path']]} />;

        //Instrument details
        const instrumentDetailsToShow = [];
        let instrumentDetailsFromBackend = instrument["details-viewer"];
        if (this.state.editorMode) {
          instrumentDetailsFromBackend = instrumentDetailsFromBackend.concat(instrument["details-editor"]);
        }
        for (let k in instrumentDetailsFromBackend) {
          k = instrumentDetailsFromBackend[k];
          if (k[1]!=="") {
            let fieldValue = k[1];
            if (fieldValue==="<copy>" && instrument.hasOwnProperty(k[0]) && instrument[k[0]]!=="" && instrument[k[0]]!=null) {
              fieldValue = instrument[k[0]];
            }
            if (fieldValue!=="<copy>") {
              instrumentDetailsToShow.push(<FormFieldUnchangeable
                      label={k[0]}
                      labelWidth="10"
                      inputWidth="15"
                      valueText={fieldValue}
                      key={fieldValue}
                  />);
            }
          }
        }

        //Instrument warnings
        const warningRows = [];
        // console.log(warningRows);
        let warningTable = <div />;
        if (instrument.hasOwnProperty("warnings") && instrument["warnings"].length>0) {
          for (const warning in instrument["warnings"]) {
            warningRows.push(
            <div className="dashlist-item" ng-repeat="dash in group.list" key={warning[0]+123}>
              <div
              className="dashlist-link dashlist-link-dash-db"
              style={{height: 50}}
              >
              <span className="warning-sign">&#9888; </span>
              <span className="warning-timestamp">{instrument["warnings"][warning][0]}     </span>
              <span className="dashlist-title">
                {instrument["warnings"][warning][1]}
              </span>
              <span className="dashlist-star" ng-click="ctrl.starDashboard(dash, $event)">
                {this.state.editorMode &&
                  <button
                  onClick={this.handleClick}
                  name="resolved-button"
                  className="btn btn-primary"
                  // value={instrument["ip"],instrument["warnings"][warning][0]]}
                  value={instrument["ip"] + "#@#" + instrument["warnings"][warning][0]}
                  >Resolved</button>}
              </span>
              </div>
            </div>);
          }
          warningTable = (
            <div className="dashlist-section" ng-repeat="category in ctrl.viewModel">
              <h6 className="dashlist-section-header">Warnings:</h6>
              <div className="scrollable-warnings">
                {warningRows}
              </div>
            </div>);
        }

        //Change displayName
        let dispplayNameInput = <div />;
        if (this.state.editorMode) {
          dispplayNameInput = (
            <div className="displayNameChangeField">
              <div className="row">
                <FormField
                      label="Change Name to:"
                      labelWidth={10}
                      placeholder={instrument["displayName"]}
                      value = {this.state.newDisplayName}
                      onChange={this.handleChange}
                  />
                <button
                onClick={this.handleClick}
                name="changeDisplayName-button"
                className="btn btn-primary"
                value={[instrument['ip'], this.state.newDisplayName]}
                >Apply</button>
              </div>
            </div>);}

        //footer buttons
        let footerButtons = <div />;
        if (this.state.editorMode) {
          footerButtons = (
            <div className="IntrumentControls-footer">
              <button
                 onClick={this.handleClick}
                 name="restart-button"
                 value={instrument["ip"]}
                 className="btn btn-primary"
                 >Restart</button>
              <button
                 onClick={this.handleClick}
                 name="destroy-button"
                 value={instrument["ip"]}
                 className="btn btn-danger"
                 >DESTROY</button>
            </div>);
        }

        placeholder = (
        <div>
          <div className="instrumentControls-header">
            {img}
          </div>
          <div className="row">
            <div className="column left-column">
              <div className="InstumentDetails scrollable-instrument_properties">
                {instrumentDetailsToShow}
              </div>
            </div>
            <div className="column right-column">
              {dispplayNameInput}
              {warningTable}
            </div>
          </div>
          {footerButtons}
        </div>);
      }

      return(
         <div>
         {placeholder}
         </div>
      );
   }
}
