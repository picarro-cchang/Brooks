let  PicarroAPI = {
    postData(url: string, data: object) {
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
                throw Error('Network POST request failed');
            }
            console.log('Posted', data);
            console.log('Response', response);
            return response;
        });
    },

    getRequest(url: string) {
        return fetch(url, {
            method: 'GET',
        })
        .then(response => {
            if (!response.ok) {
                throw Error('Network GET request failed');
            }
            console.log('Response to GET', response);
            return response;
        });
    }
};

export default PicarroAPI;
