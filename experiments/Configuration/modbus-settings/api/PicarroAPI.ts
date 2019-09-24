export const PicarroAPI = {
  postData(url: string, data: object) {
    console.log(data);
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }).then(response => {
      if (!response.ok) {
        throw Error('Network POST request failed');
      }
      return response;
    });
  },

  getRequest(url: string) {
    return fetch(url, {
      method: 'GET',
    }).then(response => {
      if (!response.ok) {
        throw Error('Network GET request failed');
      }
      return response.json();
    });
  },

  getRequestWithHeader(url: string, header: Headers) {
    return fetch(url, {
      headers: header,
      method: 'GET',
    }).then(response => {
      if (!response.ok) {
        throw Error('Network GET request failed');
      }
      return response.json();
    });
  },
};

//export default PicarroAPI;
