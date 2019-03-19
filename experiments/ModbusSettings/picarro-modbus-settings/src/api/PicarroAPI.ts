let PicarroAPI = {
  postData(url: string, data: object) {
    console.log(data);
    return fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'text/html',
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
};

export default PicarroAPI;
