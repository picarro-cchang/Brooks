import dispatcher from "../dispatcher";
import constants from "../constants";

let ApplogActionCreators = {
    processMessage(...args) {
        // message
        dispatcher.dispatch({
            type: constants.PROCESS_MESSAGE,
            payload: { args }
        });
    },
    setSocketId(...args) {
        // socketId
        dispatcher.dispatch({
            type: constants.SET_SOCKET_ID,
            payload: { args }
        });
    }
};

export default ApplogActionCreators;
