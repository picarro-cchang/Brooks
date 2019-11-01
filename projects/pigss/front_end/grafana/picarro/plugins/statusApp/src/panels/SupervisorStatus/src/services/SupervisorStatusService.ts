import { API } from './API';
import { SUPERVISOR_STATUS_API } from '../constants';

export const SupervisorStatusService = (() => {
    return {
        getStatus() {
            return API.get(SUPERVISOR_STATUS_API);
        }
    }
})();