import React, { PureComponent } from 'react';
import { PanelOptionsGroup, PanelEditorProps } from '@grafana/ui';
import { FormField, Select } from '@grafana/ui';
import { NetworkOptions, getRoute, postRoute} from '../../types';
import PicarroAPI from '../../api/PicarroAPI';
import './Network.css';

const networkOptions = [
  { value: 'Static', label: 'Static' },
  { value: 'DHCP', label: 'DHCP' }
];
const labelWidth = 8;
const regex = /\b(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b/gm;

export class NetworkPanelEditor extends PureComponent<PanelEditorProps<NetworkOptions>> {
  constructor(props) {
    super(props);
      this.handleApplyClick = this.handleApplyClick.bind(this);
      this.handleUndoClick = this.handleUndoClick.bind(this);
  };
  componentDidMount(): void {
      this.getNetworkSettings();
      this.checkInput();
  };
  onNetworkTypeChange = networkType => {
    if (networkType.value === 'DHCP') {
        this.props.onChange({ ...this.props.options, ip: ''});
        this.props.options['ip'] = '';
        this.props.options['gateway'] = '';
        this.props.options['netmask'] = '';
        this.props.options['dns'] = '';
    } else {
        this.getNetworkSettings();
    }
    this.enableUndoButton();
    this.enableApplyButton();
    this.props.onChange({ ...this.props.options, networkType: networkType.value});
  };
  onIPChange = event => {
      this.enableApplyButton();
      this.enableUndoButton();
      this.props.onChange( { ...this.props.options, ip: event.target.value });
  };
  onGatewayChange = event => {
      this.enableApplyButton();
      this.enableUndoButton();
      this.props.onChange({...this.props.options, gateway: event.target.value});
  };
  onNetmaskChange = event => {
      this.enableApplyButton();
      this.enableUndoButton();
      this.props.onChange({...this.props.options, netmask: event.target.value});
  };
  onDnsChange = event => {
      this.enableApplyButton();
      this.enableUndoButton();
      this.props.onChange({...this.props.options, dns: event.target.value});
  };
  handleApplyClick() {
    console.log('click');
    console.log(this.props.options);
    PicarroAPI.postData(postRoute, {
        'networkType': this.props.options['networkType'],
        'ip': this.props.options['ip'],
        'gateway': this.props.options['gateway'],
        'netmask': this.props.options['netmask'],
        'dns': this.props.options['dns']
    }).then(response => {
        response.text().then(text => console.log(text));
    });
    this.disableApplyButton();
    this.disableUndoButton();
  };
  handleUndoClick() {
      console.log('click');
      this.getNetworkSettings();
      this.disableApplyButton();
      this.disableUndoButton();
  };
  enableApplyButton() {
      this.props.options['applyEnabled'] = true;
  };
  enableUndoButton() {
      this.props.options['undoEnabled'] = true;
  };
  disableApplyButton() {
      this.props.options['applyEnabled'] = false;
  };
  disableUndoButton() {
      this.props.options['undoEnabled'] = false;
  };
  getNetworkSettings () {
       PicarroAPI.getRequest(getRoute).then(response => {
           response.text().then(data => {
               const jsonData = JSON.parse(data);
               this.props.onChange({ ...this.props.options, networkType: jsonData['networkType']});
               this.props.onChange({ ...this.props.options, ip: jsonData['ip']});
               this.props.onChange({ ...this.props.options, gateway: jsonData['gateway']});
               this.props.onChange({ ...this.props.options, netmask: jsonData['netmask']});
               this.props.onChange({ ...this.props.options, dns: jsonData['dns']});
           })
       })
   };
  checkInput = () => {
      let text = '192.168.1111111';
      let test = regex.test(text);
      console.log(test);
  };
  render() {
    const {
      networkType,
      ip,
      gateway,
      netmask,
      dns,
      undoEnabled,
      applyEnabled
    } = this.props.options;

    return (
        <PanelOptionsGroup title="Network Settings">
          <div className="gf-form-inline network-editor-combo-box">
            <div className="gf-form">
              <span className="gf-form-label width-8">Network Type</span>
                <Select
                    width={6}
                    options={networkOptions}
                    onChange={this.onNetworkTypeChange}
                    value={networkOptions.find(option => option.value === networkType)}
                    defaultValue={networkType}
                    backspaceRemovesValue isLoading
                />
            </div>
          </div>
          <div className="network-editor-form">
            <FormField
                label="IP"
                labelWidth={labelWidth}
                onChange={this.onIPChange}
                value={ip || ''}
            />
            <FormField
                label="Gateway"
                labelWidth={labelWidth}
                onChange={this.onGatewayChange}
                value={gateway || ''}
            />
            <FormField
                label="Netmask"
                labelWidth={labelWidth}
                onChange={this.onNetmaskChange}
                value={netmask || ''}
            />
            <FormField
                label="DNS"
                labelWidth={labelWidth}
                onChange={this.onDnsChange}
                value={dns || ''}
            />
          </div>
          <div className="network-editor-buttons">
            <button
                className="apply btn btn-primary"
                disabled={!applyEnabled}
                onClick={this.handleApplyClick}
            >
              Apply
            </button>
            <button
                className="undo btn btn-primary"
                disabled={!undoEnabled}
                onClick={this.handleUndoClick}
            >
                Undo
              </button>

          </div>
        </PanelOptionsGroup>
    );
  }
}
