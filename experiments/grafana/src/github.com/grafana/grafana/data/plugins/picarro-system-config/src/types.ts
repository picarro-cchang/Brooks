import io from 'socket.io-client';

export interface InstrumentData {
    Manufacturer: string;
    details_editor: string[][];
    details_viewer: string[][];
    displayName: string;
    ip: string;
    logo_path: string;
    position_in_rack?: any;
    status: string;
    status_color: string;
    warnings: any[];
}

export interface InstrumentsOptions {
  activeInstrument: string;
  allInstrumentsData: InstrumentData[];
  componentID: string;
}


export const instrumentsOptionsDefaults: InstrumentsOptions = {
  activeInstrument: '',
  allInstrumentsData: [],
  componentID: ""
};


export interface InstrumentsProps {
  options: InstrumentsOptions;
}

// const host = 'http://localhost:';
const host = 'http://10.100.2.93:';
const port = '1337';

export const ISPath = host + port;

export const ISGetInstruments = host + port  + '/is_get_instruments';
export const ISApplyChanges = host + port  + '/is_apply_changes';
export const ISChangeDisplayName = host + port  + '/is_changeDisplayName';
export const ISSetInstrumentPositions = host + port  + '/is_set_instrument_positions';
export const ISDestroyInstrument = host + port  + '/is_destroy_instrument';
export const ISRestartInstrument = host + port  + '/is_restart_instrument';
export const ISResolveWarning = host + port  + '/is_resolve_warning';

export const webSocket = io(host + port + '/wb');

export const picarroLogo = require("./img/picarro_logo.png");
export const teledyneLogo = require("./img/teledyne_logo.png");
export const blackMesaLogo = require("./img/black_mesa_logo.png");
export const cheeseMasterLogo = require("./img/cheese_master_logo.png");

export const logos = {
            "picarro_logo": picarroLogo,
            "teledyne_logo": teledyneLogo,
            "black_mesa_logo": blackMesaLogo,
            "cheese_master_logo": cheeseMasterLogo};
