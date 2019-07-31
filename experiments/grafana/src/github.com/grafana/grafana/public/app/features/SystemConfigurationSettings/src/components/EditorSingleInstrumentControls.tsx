import React, { Component } from 'react';
import PicarroAPI from '../api/PicarroAPI';
import {
  ISPath,
  ISDestroyInstrument,
  ISRestartInstrument,
  ISResolveWarning,
  ISChangeDisplayName,
  picarroLogo,
  teledyneLogo,
  blackMesaLogo,
  cheeseMasterLogo,
} from '../types';

import { FormLabel } from '@grafana/ui';
import { Input } from 'app/core/components/Form/Input';

const FormFieldUnchangeable = _a => {
  const label = _a.label;
  const labelWidth = _a.labelWidth;
  const inputWidth = _a.inputWidth;
  const valueText = _a.valueText;

  return (
    <div className="form-field">
      <FormLabel width={labelWidth}> {label}</FormLabel>
      <div className={'gf-form-input width-' + inputWidth}>{valueText}</div>
    </div>
  );
};

const logos = {
  picarro_logo: picarroLogo,
  teledyne_logo: teledyneLogo,
  black_mesa_logo: blackMesaLogo,
  cheese_master_logo: cheeseMasterLogo,
};

export class EditorSingleInstrumentControls extends Component<any, any> {
  constructor(props) {
    super(props);

    this.handleChange = this.handleChange.bind(this);
    this.handleClick = this.handleClick.bind(this);
    this.state = {
      parent: this.props.parent,
      newDisplayName: '',
      editorMode: this.props.editorMode,
      enableApply: false,
      showNewNamePrompt: false,
    };
  }

  handleChange(event) {
    this.setState({ newDisplayName: event.target.value });
    const newName = event.target.value;
    if (newName.length > 0) {
      if (this.newInstrumentNameValidation(newName)) {
        this.setState({ enableApply: true });
        this.setState({ showNewNamePrompt: false });
      } else {
        this.setState({ enableApply: false });
        this.setState({ showNewNamePrompt: true });
      }
    } else {
      this.setState({ enableApply: false });
      this.setState({ showNewNamePrompt: false });
    }
  }

  newInstrumentNameValidation(newName) {
    const instrumentNameAlphabet = /^[0-9a-zA-Z_]+$/;
    return instrumentNameAlphabet.test(newName) && newName.length <= 32;
  }

  handleClick(event) {
    const { value, name } = event.target;

    if (name === 'destroy-button') {
      PicarroAPI.postData(ISDestroyInstrument, {
        ip: value,
      });
    } else if (name === 'restart-button') {
      PicarroAPI.postData(ISRestartInstrument, {
        ip: value,
      });
    } else if (name === 'resolved-button') {
      const array = value.split('#@#');
      PicarroAPI.postData(ISResolveWarning, {
        ip: array[0],
        warning: array[1],
      });
    } else if (name === 'changeDisplayName-button') {
      const array = value.split(',');
      PicarroAPI.postData(ISChangeDisplayName, {
        ip: array[0],
        newDisplayName: array[1],
      });
    } else if (name === 'restart-button') {
      PicarroAPI.postData(ISRestartInstrument, {
        ip: value,
      });
    } else if (name.indexOf('@') > -1) {
      const buttonName = name.split('@')[0];
      const endpoint = ISPath + '/' + name.split('@')[1];
      PicarroAPI.postData(endpoint, {
        ip: value,
        buttonName: buttonName,
      });
    }
  }

  render() {
    const instrument = this.props.activeInstrument;
    let placeholder = <div />;
    if (instrument != null) {
      //Instrument logo
      const img = <img height="40" src={logos[instrument['logo_path']]} />;

      //Instrument details
      const instrumentDetailsToShow = [];
      let instrumentDetailsFromBackend = instrument['details-viewer'];
      if (this.state.editorMode) {
        instrumentDetailsFromBackend = instrumentDetailsFromBackend.concat(instrument['details-editor']);
      }
      for (let k in instrumentDetailsFromBackend) {
        k = instrumentDetailsFromBackend[k];
        if (k[1] !== '') {
          let fieldValue = k[1];
          if (
            fieldValue === '<copy>' &&
            instrument.hasOwnProperty(k[0]) &&
            instrument[k[0]] !== '' &&
            instrument[k[0]] != null
          ) {
            fieldValue = instrument[k[0]];
          }
          if (fieldValue !== '<copy>') {
            instrumentDetailsToShow.push(
              <FormFieldUnchangeable
                label={k[0]}
                labelWidth="10"
                inputWidth="15"
                valueText={fieldValue}
                key={instrument['ip'] + '_' + k + '_' + fieldValue}
              />
            );
          }
        }
      }

      //Instrument warnings
      const warningRows = [];
      // console.log(warningRows);
      let warningTable = <div />;
      if (instrument.hasOwnProperty('warnings') && instrument['warnings'].length > 0) {
        for (const warning in instrument['warnings']) {
          warningRows.push(
            <div className="dashlist-item" ng-repeat="dash in group.list" key={warning[0] + 123}>
              <div className="dashlist-link dashlist-link-dash-db" style={{ height: 50 }}>
                <span className="warning-sign">&#9888; </span>
                <span className="warning-timestamp">{instrument['warnings'][warning][0]} </span>
                <span className="dashlist-title">{instrument['warnings'][warning][1]}</span>
                <span className="dashlist-star" ng-click="ctrl.starDashboard(dash, $event)">
                  {this.state.editorMode && (
                    <button
                      onClick={this.handleClick}
                      name="resolved-button"
                      className="btn btn-primary"
                      // value={instrument["ip"],instrument["warnings"][warning][0]]}
                      value={instrument['ip'] + '#@#' + instrument['warnings'][warning][0]}
                    >
                      Resolved
                    </button>
                  )}
                </span>
              </div>
            </div>
          );
        }
        warningTable = (
          <div className="dashlist-section" ng-repeat="category in ctrl.viewModel">
            <h6 className="dashlist-section-header">Warnings:</h6>
            <div className="scrollable-warnings">{warningRows}</div>
          </div>
        );
      }
      //Change displayName
      let dispplayNameInput = <div />;
      if (this.state.editorMode) {
        dispplayNameInput = (
          <form name="displayNameChangeForm" className="gf-form-group">
            <div className="gf-form max-width-30">
              <FormLabel tooltip="Allowed characters are [A-Z,a-z,0-9,_]">Change Name to:</FormLabel>
              <Input
                type="text"
                className="gf-form-input max-width-15"
                placeholder={instrument['displayName']}
                value={this.state.newDisplayName}
                onChange={this.handleChange}
                style={this.state.showNewNamePrompt ? { border: '1px solid red' } : {}}
              />
            </div>
            <button
              onClick={this.handleClick}
              name="changeDisplayName-button"
              className="btn btn-primary"
              disabled={!this.state.enableApply}
              value={[instrument['ip'], this.state.newDisplayName]}
            >
              Apply
            </button>
          </form>
        );
      }

      //footer buttons
      let footerButtonsRaw = <div />;
      if (this.state.editorMode) {
        const buttonsArray = [];
        for (let i in instrument['ui-buttons']) {
          const button_i = instrument['ui-buttons'][i];
          buttonsArray.push(
            <button
              onClick={this.handleClick}
              name={button_i['name'] + '@' + button_i['endpoint']}
              value={instrument['ip']}
              key={'button_' + button_i['name'] + '_' + instrument['ip']}
              className={button_i['color'] === 'green' ? 'btn btn-primary' : 'btn btn-danger'}
            >
              {button_i['displayName']}
            </button>
          );
        }

        footerButtonsRaw = <div className="IntrumentControls-footer">{buttonsArray}</div>;
      }

      placeholder = (
        <div>
          <div className="instrumentControls-header">{img}</div>
          <div className="row">
            <div className="column left-column">
              <div className="InstumentDetails scrollable-instrument_properties">{instrumentDetailsToShow}</div>
            </div>
            <div className="column right-column">
              {dispplayNameInput}
              {warningTable}
            </div>
          </div>
          {footerButtonsRaw}
        </div>
      );
    }

    return <div>{placeholder}</div>;
  }
}
