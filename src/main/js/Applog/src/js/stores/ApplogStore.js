import ApplogActionCreators from "../actions/ApplogActionCreators";
import {Store} from "flux/utils";
import constants from "../constants";
import dispatcher from "../dispatcher";
import io from "socket.io-client";

class ApplogStore extends Store {
    constructor(...args) {
        super(...args);
        this.store = {
            socketId: null
        };
        // this.socket = io("http://localhost:3000", {transports: ["websocket"]});
        this.socket = io("http://" + window.location.host, {transports: ["websocket"]});
        this.socket.on("connect", () => console.log("Web socket connected"));
        this.socket.on("applog", (message) => console.log(message));
        this.socket.on("socket_id", (data) => { console.log("socket_id: ", data); ApplogActionCreators.setSocketId(data); });
    }

    getState() {
        return this.store;
    }

    setSocketId(socketId) {
        this.store.socketId = socketId;
    }

    __onDispatch(action) {
        switch (action.type) {
        case constants.SET_SOCKET_ID:
            this.setSocketId(...action.payload.args);
            break;
        default:
            break;
        }
        this.__emitChange();
    }
}

export default new ApplogStore(dispatcher);