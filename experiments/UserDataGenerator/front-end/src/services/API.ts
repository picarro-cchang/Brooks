export const API = {
  get(url: string) {
    return fetch(url, { method: 'GET' }).then(response => {
      if (!response.ok) {
        throw Error('Netwoek GET request failed.');
      }
      return response;
    });
  },
};
