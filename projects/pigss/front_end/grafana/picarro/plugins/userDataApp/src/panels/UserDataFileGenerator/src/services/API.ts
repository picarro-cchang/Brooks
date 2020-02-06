import { notifyError } from '../utils/Notifications';

export const API = {
  get(url: string) {
    return fetch(url, { method: 'GET' })
      .then(response => {
        if (!response.ok) {
          throw Error('Network GET request failed.');
        }
        return response;
      })
      .catch(err => {
        notifyError(err.message);
        throw Error('Network GET request failed.');
      });
  },
  post(url: string, data: object={}) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    })
      .then(response => {
        if (!response.ok) {
          notifyError('Network POST request failed')
          throw Error('Network POST request failed');
        }
        return response;
      });
  },
};
