import { notifyError } from '../utils/Notifications';

export const API = {
    get(url: string) {
        return fetch(url, {method: 'GET'})
            .then(response => {
                if (!response.ok) {
                    throw Error("Network GET request failed.");
                }
                return response;
            })
            .catch(err => {
                notifyError(err.message);
                throw Error("Network GET request failed.")
            })
    }
}