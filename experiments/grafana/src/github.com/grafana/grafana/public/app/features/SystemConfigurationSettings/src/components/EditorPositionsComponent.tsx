import React, { Component  } from 'react';
import PicarroAPI from "../api/PicarroAPI";
import {
  PanelOptionsGroup,
} from '@grafana/ui';
import {
  ISGetInstruments,
  ISApplyChanges,
  } from '../types';

export class EditorPositionsComponent extends Component<any, any>   {
  constructor(props) {
    super(props);
    this.state = {
      slotsCount: this.props.slotsCount,
      allInstrumentsData: [],
      dropListsCurrentOptionsIP: [],
      dropListsCurrentOptionsIPPopulated: false,
      applyEnabled: false,
      undoEnabled: false,
      statusMessage: null,
    };
  }

  componentDidMount() {
    const repupulateFields = true;
    this.updateIntruments(repupulateFields);
  }

  updateIntruments(repupulateFields) {
    const newState = { ...this.state };
    PicarroAPI.getRequest(ISGetInstruments).then(response => {
        response.text().then(data => {
            const jsonData = JSON.parse(data);
            newState.allInstrumentsData = jsonData;
            this.setState(newState);
            if (repupulateFields) {
              this.populateFields();
            }
        });
    });
  }

  populateFields() {
    const tempDropListInitialOptionsIP = new Array(this.state.slotsCount).fill("");

    // find which instruments are within which positions right now according to backend
    for (let i = 0; i < this.state.allInstrumentsData.length; i++) {
      if (this.state.allInstrumentsData[i]["position_in_rack"]!=null) {
        tempDropListInitialOptionsIP[this.state.allInstrumentsData[i]["position_in_rack"]-1] = this.state.allInstrumentsData[i]["ip"];
      }
    }

    // set as current and as initial
    this.setState({dropListsCurrentOptionsIP: tempDropListInitialOptionsIP});
    this.setState({dropListsCurrentOptionsIPPopulated: true});
    this.setState({undoEnabled: false});
    this.setState({applyEnabled: false});
  }

  checkForDuplicates() {
    // console.log("IPS");
    const ips = this.state.dropListsCurrentOptionsIP.map(w=> w);
    // console.log(ips);
    const duplicates = ips.reduce((acc, el, i, arr) => {
      if (arr.indexOf(el) !== i && acc.indexOf(el) < 0) {
        acc.push(el);
      } return acc;
    }, []);
    if (duplicates.length>0 && ! (duplicates.length===1 && duplicates[0]===null)) {
      return duplicates;
    } else {
      return false;
    }
  }

    handleChange(field, event) {
      const newFields = {...this.state};
      newFields.dropListsCurrentOptionsIP[field] = event.target.value;
      this.setState(newFields);

      const dups = this.checkForDuplicates();
      if (dups && (dups[0]!==""&& dups.length === 1 )) {
        this.setState({"statusMessage": [1, "Duplicates detected"]});
        this.setState({"applyEnabled": false});
      } else {
        this.setState({"statusMessage": null});
        this.setState({"applyEnabled": true});
      }
        this.setState({"undoEnabled": true});
    }


  handleUndoClick = () => {
    this.updateIntruments(true);
  }

  applyPositionsButtonHandle = () => {
      const updatedInstruments = this.state.allInstrumentsData;
      for (let j = 0; j < this.state.allInstrumentsData.length; j++) {
          updatedInstruments[j].position_in_rack = null;
        }

      for (let i = 0; i < this.state.dropListsCurrentOptionsIP.length; i++) {
        for (let j = 0; j < this.state.allInstrumentsData.length; j++) {
          if (this.state.dropListsCurrentOptionsIP[i]===this.state.allInstrumentsData[j]["ip"]) {
            updatedInstruments[j]["position_in_rack"] = i+1;
          }
        }
      }

      this.setState({allInstrumentsData: updatedInstruments});
      PicarroAPI.postData(ISApplyChanges, this.state.allInstrumentsData)
      .then(response => response.json())
      .then(data => {
        this.setState({"position-message": [0, "Accepted"]});
        this.setState({"undoEnabled": false});
        this.setState({"applyEnabled": false});
      });
    }

  render() {
    const dropLists = [];
    if (this.state.allInstrumentsData.length>0 && this.state.dropListsCurrentOptionsIPPopulated) {
      for (let listN = 0; listN < this.state.slotsCount; listN++) {
        const listOfOptions2 = [];
        for (let i = 0; i < this.state.allInstrumentsData.length; i++) {
            listOfOptions2.push(<option
              value = {this.state.allInstrumentsData[i]["ip"]}
              key = {this.state.allInstrumentsData[i]["displayName"]}
              > {this.state.allInstrumentsData[i]["displayName"]}
              </option>);
        }
        listOfOptions2.push(<option
              value = {""}
              key = {"Empty"}
              > Empty
              </option>);

        dropLists.push(<div key={"dropListNumber_" + (listN+1)}>
            <span className="gf-form-label width-10">
              Position {listN+1}
            </span>
          <select
            className="input-small gf-form-input"
            onChange={this.handleChange.bind(this,
              listN)}
            value={this.state.dropListsCurrentOptionsIP[listN]}
            >
            {listOfOptions2}
          </select>
          </div>);
      }
    }

    // position message
    let positionMessage = <p></p>;
    if (this.state.statusMessage) {
        if (this.state.statusMessage[0]===0) {
          positionMessage = <p className="positions-message accepted show">
          {this.state.statusMessage[1]}
          </p>;
            }
        if (this.state.statusMessage[0]===1) {
          positionMessage = <p className="positions-message error show">
          {this.state.statusMessage[1]}
          </p>;
            }
    }
    return (
      <div>
        <PanelOptionsGroup title="Positions">
          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
            {dropLists}
            </div>
          </div>
          <div className="gf-form-button-row">
            <button
              className="btn btn-primary"
              disabled={!this.state.applyEnabled}
              onClick={this.applyPositionsButtonHandle}>
              Apply
            </button>
            <button
                className="undo-btn btn btn-primary"
                disabled={!this.state.undoEnabled}
                onClick={this.handleUndoClick}>
                Undo
            </button>
          </div>
          {positionMessage}
        </PanelOptionsGroup>
      </div>
    );
  }
}
