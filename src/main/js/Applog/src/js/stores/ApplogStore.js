import ApplogActionCreators from "../actions/ApplogActionCreators";
import {Store} from "flux/utils";
import constants from "../constants";
import dispatcher from "../dispatcher";
import io from "socket.io-client";
import _ from "lodash";

class ApplogStore extends Store {
    constructor(...args) {
        super(...args);
        this.store = {
            socketId: null,
            sourceData: {}, // Messages for sources, keyed by sourceName
            sourceNames: [] // Array of source names
        };
        // this.socket = io("http://localhost:3000", {transports: ["websocket"]});
        this.socket = io("http://" + window.location.host, {transports: ["websocket"]});
        this.socket.on("connect", () => console.log("Web socket connected"));
        this.socket.on("applog", (message) => ApplogActionCreators.processMessage(message));
        this.socket.on("socket_id", (data) => { console.log("socket_id: ", data); ApplogActionCreators.setSocketId(data); });
    }

    getState() {
        return this.store;
    }

    processMessage(message) {
        let MAX_LENGTH = 65536;
        let components = message.message.split(":", 2);
        let source = components[0];
        if (!_.includes(this.store.sourceNames, source)) {
            this.store.sourceData[source] = "";
            this.store.sourceNames.push(source);
            this.store.sourceNames.sort();
        }
        this.store.sourceData[source] += components[1];
        if (this.store.sourceData[source].length > MAX_LENGTH) {
            let m = this.store.sourceData[source].slice(0,MAX_LENGTH >> 1).lastIndexOf("\n");
            if (m < 0) {
                m = MAX_LENGTH >> 1;
            }
            this.store.sourceData[source] = this.store.sourceData[source].slice(m);
        }
    }

    setSocketId(socketId) {
        this.store.socketId = socketId;
    }

    __onDispatch(action) {
        switch (action.type) {
        case constants.PROCESS_MESSAGE:
            this.processMessage(...action.payload.args);
            break;
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