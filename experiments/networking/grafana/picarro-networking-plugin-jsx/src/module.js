import React, { Component } from 'react'
import { ReactPanelPlugin } from '@grafana/ui'
import App from './components/App'
import { NetworkSettingsEditor } from './components/NetworkSettingsEditor'

export class MyPanel extends Component {
  render() {
    return (
    <div><App /></div>
    )
  }
}



export const reactPanel = new ReactPanelPlugin(MyPanel);
reactPanel.setEditor(NetworkSettingsEditor);
reactPanel.setDefaults({
  networkType: "",
  ip: "",
  gateway: "",
  netmask: "",
  dns: ""
});
