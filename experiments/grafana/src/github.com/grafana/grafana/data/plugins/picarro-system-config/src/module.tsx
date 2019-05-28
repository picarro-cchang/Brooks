import { ReactPanelPlugin } from '@grafana/ui';
// import { NetworkPanel } from './components/Network/NetworkPanel';
import {InstrumentsPanel} from "./components/InstrumentsPanel"
import { instrumentsOptionsDefaults, InstrumentsOptions } from './types';
import "./css/style.css"


export const reactPanel = new ReactPanelPlugin<InstrumentsOptions>(InstrumentsPanel);
reactPanel.setDefaults(instrumentsOptionsDefaults);
