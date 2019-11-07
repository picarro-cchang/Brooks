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
                throw Error('Network GET request failed.');
            });
    },
};
