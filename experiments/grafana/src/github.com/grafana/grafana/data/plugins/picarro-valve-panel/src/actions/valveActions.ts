import PicarroAPI from '../api/PicarroAPI';

export function setValveMode(mode: number) {
  return {
    type: 'SET_VALVE_MODE',
    payload: PicarroAPI.postData('http://localhost:8888/valve_mode', { mode })
      .then(response => response.json())
      .then(response => response.mode),
  };
}

export function getValveMode() {
  return {
    type: 'GET_VALVE_MODE',
    payload: PicarroAPI.getRequest('http://localhost:8888/valve_mode')
      .then(response => response.json())
      .then(response => response.mode),
  };
}
