import dispatcher from "../dispatcher";
import constants from "../constants";

let ApplogActionCreators = {
    setSocketId(...args) {
        // socketId
        dispatcher.dispatch({
            type: constants.SET_SOCKET_ID,
            payload: { args }
        });
    }
};

export default ApplogActionCreators;
